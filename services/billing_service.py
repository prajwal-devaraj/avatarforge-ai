from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from urllib import parse, request as urlrequest

from flask import current_app
from sqlalchemy import func, select

from models import ApiKey, ApiUsage, Generation, Subscription, User


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    price_monthly_cents: int
    generation_quota: int
    api_rate_limit_per_minute: int
    features: tuple[str, ...]


PLANS: dict[str, Plan] = {
    "free": Plan(
        code="free",
        name="Free",
        price_monthly_cents=0,
        generation_quota=25,
        api_rate_limit_per_minute=10,
        features=("25 generations / month", "Classic + mock AI modes", "Private generation history"),
    ),
    "pro": Plan(
        code="pro",
        name="Pro",
        price_monthly_cents=1200,
        generation_quota=500,
        api_rate_limit_per_minute=60,
        features=("500 generations / month", "Developer API access", "Higher rate limits", "Priority processing ready"),
    ),
    "business": Plan(
        code="business",
        name="Business",
        price_monthly_cents=3900,
        generation_quota=2500,
        api_rate_limit_per_minute=180,
        features=("2,500 generations / month", "Team-scale API quota", "Highest rate limits", "Production support ready"),
    ),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _period_now() -> str:
    return _now().strftime("%Y-%m")


def get_subscription(user_id: str, *, create: bool = True) -> Subscription | None:
    db = current_app.extensions["db_session"]
    subscription = db.scalar(select(Subscription).where(Subscription.user_id == user_id))
    if subscription is None and create:
        subscription = Subscription(user_id=user_id, plan_code="free", status="active", provider="internal")
        db.add(subscription)
        db.commit()
    return subscription


def get_plan_for_user(user_id: str) -> Plan:
    subscription = get_subscription(user_id)
    code = "free"
    if subscription is not None and subscription.status in {"active", "trialing"}:
        code = subscription.plan_code if subscription.plan_code in PLANS else "free"
    plan = PLANS[code]
    if code == "free":
        return replace(
            plan,
            generation_quota=int(current_app.config.get("API_MONTHLY_GENERATION_QUOTA", plan.generation_quota)),
            api_rate_limit_per_minute=int(current_app.config.get("API_RATE_LIMIT_PER_MINUTE", plan.api_rate_limit_per_minute)),
        )
    quota_key = f"PLAN_{code.upper()}_GENERATION_QUOTA"
    rate_key = f"PLAN_{code.upper()}_RATE_LIMIT_PER_MINUTE"
    return replace(
        plan,
        generation_quota=int(current_app.config.get(quota_key, plan.generation_quota)),
        api_rate_limit_per_minute=int(current_app.config.get(rate_key, plan.api_rate_limit_per_minute)),
    )


def plan_limits_for_user(user_id: str) -> tuple[int, int]:
    plan = get_plan_for_user(user_id)
    return plan.generation_quota, plan.api_rate_limit_per_minute


def usage_summary(user_id: str) -> dict:
    db = current_app.extensions["db_session"]
    period = _period_now()
    plan = get_plan_for_user(user_id)
    key_ids = list(db.scalars(select(ApiKey.id).where(ApiKey.user_id == user_id)).all())
    api_requests = 0
    api_generations = 0
    if key_ids:
        request_total, generation_total = db.execute(
            select(
                func.coalesce(func.sum(ApiUsage.request_count), 0),
                func.coalesce(func.sum(ApiUsage.generation_count), 0),
            ).where(ApiUsage.api_key_id.in_(key_ids), ApiUsage.period == period)
        ).one()
        api_requests = int(request_total or 0)
        api_generations = int(generation_total or 0)

    start = datetime(_now().year, _now().month, 1, tzinfo=timezone.utc)
    saved_generations = int(
        db.scalar(select(func.count()).select_from(Generation).where(Generation.user_id == user_id, Generation.created_at >= start))
        or 0
    )
    used = max(api_generations, saved_generations)
    return {
        "period": period,
        "plan": plan,
        "api_requests": api_requests,
        "api_generations": api_generations,
        "saved_generations": saved_generations,
        "generation_used": used,
        "generation_quota": plan.generation_quota,
        "generation_remaining": max(0, plan.generation_quota - used),
    }


def set_plan(user_id: str, plan_code: str, *, provider: str = "internal", status: str = "active", provider_customer_id: str | None = None, provider_subscription_id: str | None = None, current_period_end: datetime | None = None) -> Subscription:
    if plan_code not in PLANS:
        raise ValueError("Unknown plan")
    subscription = get_subscription(user_id)
    assert subscription is not None
    subscription.plan_code = plan_code
    subscription.status = status
    subscription.provider = provider
    if provider_customer_id is not None:
        subscription.provider_customer_id = provider_customer_id
    if provider_subscription_id is not None:
        subscription.provider_subscription_id = provider_subscription_id
    subscription.current_period_end = current_period_end
    subscription.updated_at = _now()
    current_app.extensions["db_session"].commit()
    return subscription


def _stripe_request(path: str, payload: dict[str, str]) -> dict:
    secret = current_app.config.get("STRIPE_SECRET_KEY", "")
    if not secret:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    body = parse.urlencode(payload).encode("utf-8")
    req = urlrequest.Request(
        f"https://api.stripe.com/v1/{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=20) as response:  # noqa: S310 - fixed Stripe host
        return json.loads(response.read().decode("utf-8"))


def start_checkout(user: User, plan_code: str) -> str:
    if plan_code not in {"pro", "business"}:
        raise ValueError("Checkout is only available for paid plans")
    provider = str(current_app.config.get("BILLING_PROVIDER", "mock")).lower()
    if provider == "mock":
        set_plan(user.id, plan_code, provider="mock")
        return "/account/billing?upgraded=1"
    if provider != "stripe":
        raise RuntimeError("Unsupported billing provider")

    price_id = current_app.config.get(f"STRIPE_PRICE_{plan_code.upper()}", "")
    if not price_id:
        raise RuntimeError(f"Stripe price is not configured for {plan_code}")
    base_url = current_app.config.get("APP_BASE_URL", "").rstrip("/")
    if not base_url:
        raise RuntimeError("APP_BASE_URL is required for Stripe checkout")

    subscription = get_subscription(user.id)
    payload = {
        "mode": "subscription",
        "success_url": f"{base_url}/account/billing?checkout=success",
        "cancel_url": f"{base_url}/account/billing?checkout=cancelled",
        "client_reference_id": user.id,
        "customer_email": user.email,
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "metadata[user_id]": user.id,
        "metadata[plan_code]": plan_code,
        "subscription_data[metadata][user_id]": user.id,
        "subscription_data[metadata][plan_code]": plan_code,
    }
    if subscription and subscription.provider_customer_id:
        payload.pop("customer_email", None)
        payload["customer"] = subscription.provider_customer_id
    session = _stripe_request("checkout/sessions", payload)
    return session["url"]


def start_billing_portal(user_id: str) -> str:
    subscription = get_subscription(user_id)
    provider = str(current_app.config.get("BILLING_PROVIDER", "mock")).lower()
    if provider == "mock":
        return "/account/billing"
    if not subscription or not subscription.provider_customer_id:
        raise RuntimeError("No Stripe customer exists for this account")
    base_url = current_app.config.get("APP_BASE_URL", "").rstrip("/")
    session = _stripe_request("billing_portal/sessions", {
        "customer": subscription.provider_customer_id,
        "return_url": f"{base_url}/account/billing",
    })
    return session["url"]


def verify_stripe_signature(payload: bytes, signature_header: str) -> bool:
    secret = str(current_app.config.get("STRIPE_WEBHOOK_SECRET", ""))
    if not secret or not signature_header:
        return False
    pieces = {}
    for part in signature_header.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            pieces.setdefault(key.strip(), []).append(value.strip())
    timestamp_values = pieces.get("t", [])
    signatures = pieces.get("v1", [])
    if not timestamp_values or not signatures:
        return False
    timestamp = timestamp_values[0]
    try:
        if abs(int(_now().timestamp()) - int(timestamp)) > 300:
            return False
    except ValueError:
        return False
    signed_payload = timestamp.encode("utf-8") + b"." + payload
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in signatures)


def handle_stripe_event(event: dict) -> None:
    event_type = event.get("type", "")
    obj = event.get("data", {}).get("object", {}) or {}
    metadata = obj.get("metadata", {}) or {}
    user_id = metadata.get("user_id")
    plan_code = metadata.get("plan_code")

    if event_type == "checkout.session.completed":
        user_id = obj.get("client_reference_id") or user_id
        if user_id and plan_code in PLANS:
            set_plan(
                user_id,
                plan_code,
                provider="stripe",
                status="active",
                provider_customer_id=obj.get("customer"),
                provider_subscription_id=obj.get("subscription"),
            )
        return

    if event_type.startswith("customer.subscription."):
        provider_subscription_id = obj.get("id")
        db = current_app.extensions["db_session"]
        subscription = None
        if provider_subscription_id:
            subscription = db.scalar(select(Subscription).where(Subscription.provider_subscription_id == provider_subscription_id))
        if subscription is None and user_id:
            subscription = get_subscription(user_id)
        if subscription is None:
            return
        item_data = ((obj.get("items") or {}).get("data") or [])
        price_id = (((item_data[0] if item_data else {}).get("price") or {}).get("id"))
        if price_id:
            if price_id == current_app.config.get("STRIPE_PRICE_PRO"):
                plan_code = "pro"
            elif price_id == current_app.config.get("STRIPE_PRICE_BUSINESS"):
                plan_code = "business"
        subscription.plan_code = plan_code if plan_code in PLANS else subscription.plan_code
        subscription.status = obj.get("status") or subscription.status
        subscription.provider = "stripe"
        subscription.provider_customer_id = obj.get("customer") or subscription.provider_customer_id
        subscription.provider_subscription_id = provider_subscription_id or subscription.provider_subscription_id
        period_end = obj.get("current_period_end")
        if period_end:
            subscription.current_period_end = datetime.fromtimestamp(int(period_end), tz=timezone.utc)
        if event_type == "customer.subscription.deleted":
            subscription.plan_code = "free"
            subscription.status = "canceled"
        subscription.updated_at = _now()
        db.commit()
