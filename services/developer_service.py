from __future__ import annotations

import hashlib
import secrets
import threading
import time
from datetime import datetime, timezone

from flask import current_app
from sqlalchemy import select

from models import ApiKey, ApiUsage

_memory_lock = threading.Lock()
_memory_windows: dict[str, tuple[int, int]] = {}


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _period_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def create_api_key(*, user_id: str, name: str) -> tuple[ApiKey, str]:
    label = (name or "Default").strip()[:80] or "Default"
    raw_key = "af_live_" + secrets.token_urlsafe(32)
    record = ApiKey(
        user_id=user_id,
        name=label,
        key_prefix=raw_key[:16],
        key_hash=_hash_key(raw_key),
    )
    db = current_app.extensions["db_session"]
    db.add(record)
    db.commit()
    return record, raw_key


def authenticate_api_key(raw_key: str | None) -> ApiKey | None:
    if not raw_key or not raw_key.startswith("af_live_"):
        return None
    db = current_app.extensions["db_session"]
    record = db.scalar(select(ApiKey).where(ApiKey.key_hash == _hash_key(raw_key), ApiKey.revoked_at.is_(None)))
    if record is None:
        return None
    record.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return record


def list_api_keys(user_id: str) -> list[ApiKey]:
    db = current_app.extensions["db_session"]
    return list(db.scalars(select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())).all())


def revoke_api_key(*, user_id: str, key_id: str) -> bool:
    db = current_app.extensions["db_session"]
    record = db.scalar(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id))
    if record is None:
        return False
    if record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return True


def usage_for_key(api_key_id: str, *, period: str | None = None) -> ApiUsage | None:
    db = current_app.extensions["db_session"]
    return db.scalar(select(ApiUsage).where(ApiUsage.api_key_id == api_key_id, ApiUsage.period == (period or _period_now())))


def increment_usage(api_key_id: str, *, generation: bool = False) -> ApiUsage:
    db = current_app.extensions["db_session"]
    period = _period_now()
    usage = db.scalar(select(ApiUsage).where(ApiUsage.api_key_id == api_key_id, ApiUsage.period == period))
    if usage is None:
        usage = ApiUsage(api_key_id=api_key_id, period=period, request_count=0, generation_count=0)
        db.add(usage)
    usage.request_count += 1
    if generation:
        usage.generation_count += 1
    usage.updated_at = datetime.now(timezone.utc)
    db.commit()
    return usage


def generation_quota_remaining(api_key_id: str) -> tuple[int, int, int]:
    quota = int(current_app.config.get("API_MONTHLY_GENERATION_QUOTA", 100))
    usage = usage_for_key(api_key_id)
    used = usage.generation_count if usage else 0
    return quota, used, max(0, quota - used)


def quota_allows_generation(api_key_id: str) -> bool:
    quota, used, _ = generation_quota_remaining(api_key_id)
    return used < quota


def _memory_rate_limit(identity: str, limit: int) -> tuple[bool, int]:
    now = int(time.time())
    window = now // 60
    key = f"{identity}:{window}"
    with _memory_lock:
        count, existing_window = _memory_windows.get(key, (0, window))
        if existing_window != window:
            count = 0
        count += 1
        _memory_windows[key] = (count, window)
    retry_after = 60 - (now % 60)
    return count <= limit, retry_after


def check_rate_limit(identity: str) -> tuple[bool, int]:
    limit = int(current_app.config.get("API_RATE_LIMIT_PER_MINUTE", 30))
    if limit <= 0:
        return True, 0

    backend = str(current_app.config.get("RATE_LIMIT_BACKEND", "memory")).lower()
    if backend == "redis":
        try:
            import redis

            client = redis.from_url(current_app.config["REDIS_URL"])
            now = int(time.time())
            window = now // 60
            key = f"avatarforge:ratelimit:{identity}:{window}"
            count = client.incr(key)
            if count == 1:
                client.expire(key, 70)
            return count <= limit, 60 - (now % 60)
        except Exception:
            current_app.logger.exception("Redis rate limiter failed; falling back to memory")

    return _memory_rate_limit(identity, limit)
