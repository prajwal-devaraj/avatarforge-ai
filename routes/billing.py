from __future__ import annotations

import json

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import User
from services.billing_service import PLANS, get_subscription, handle_stripe_event, start_billing_portal, start_checkout, usage_summary, verify_stripe_signature
from utils.auth import login_required
from utils.security import valid_csrf_token


billing_bp = Blueprint("billing", __name__)


@billing_bp.get("/account/billing")
@login_required
def billing_dashboard():
    subscription = get_subscription(g.user.id)
    return render_template(
        "billing.html",
        plans=PLANS.values(),
        subscription=subscription,
        usage=usage_summary(g.user.id),
        billing_provider=current_app.config.get("BILLING_PROVIDER", "mock"),
    )


@billing_bp.post("/account/billing/checkout/<plan_code>")
@login_required
def billing_checkout(plan_code: str):
    if not valid_csrf_token(request.form.get("_csrf")):
        flash("Your session token expired. Please try again.", "error")
        return redirect(url_for("billing.billing_dashboard"))
    try:
        destination = start_checkout(g.user, plan_code)
    except (ValueError, RuntimeError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("billing.billing_dashboard"))
    return redirect(destination)


@billing_bp.post("/account/billing/portal")
@login_required
def billing_portal():
    if not valid_csrf_token(request.form.get("_csrf")):
        flash("Your session token expired. Please try again.", "error")
        return redirect(url_for("billing.billing_dashboard"))
    try:
        destination = start_billing_portal(g.user.id)
    except RuntimeError as exc:
        flash(str(exc), "error")
        return redirect(url_for("billing.billing_dashboard"))
    return redirect(destination)


@billing_bp.route("/account/settings", methods=["GET", "POST"])
@login_required
def account_settings():
    if request.method == "POST":
        if not valid_csrf_token(request.form.get("_csrf")):
            flash("Your session token expired. Please try again.", "error")
            return render_template("settings.html"), 400

        action = request.form.get("action", "profile")
        db = current_app.extensions["db_session"]
        if action == "profile":
            email = request.form.get("email", "").strip().lower()
            if "@" not in email or len(email) > 320:
                flash("Enter a valid email address.", "error")
            else:
                g.user.email = email
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    flash("That email address is already in use.", "error")
                else:
                    flash("Account email updated.", "success")
        elif action == "password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            if not g.user.check_password(current_password):
                flash("Current password is incorrect.", "error")
            elif len(new_password) < 8:
                flash("New password must be at least 8 characters.", "error")
            else:
                g.user.set_password(new_password)
                db.commit()
                flash("Password updated.", "success")
        return redirect(url_for("billing.account_settings"))

    return render_template("settings.html")


@billing_bp.post("/api/v1/billing/webhook")
def billing_webhook():
    payload = request.get_data(cache=False)
    signature = request.headers.get("Stripe-Signature", "")
    if not verify_stripe_signature(payload, signature):
        return {"error": "invalid_signature"}, 400
    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"error": "invalid_payload"}, 400
    handle_stripe_event(event)
    return {"received": True}, 200
