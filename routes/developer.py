from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, g, request

from services.developer_service import create_api_key, generation_quota_remaining, list_api_keys, revoke_api_key, usage_for_key
from utils.api_response import api_error, api_success
from utils.security import valid_csrf_token


developer_bp = Blueprint("developer", __name__, url_prefix="/api/v1/developer")


def _require_session_user():
    if g.get("user") is None:
        return api_error("Sign in to manage developer API keys.", code="authentication_required", status=401)
    return None


def _require_csrf():
    token = request.headers.get("X-CSRF-Token") or request.form.get("_csrf")
    if not valid_csrf_token(token):
        return api_error("Invalid or expired CSRF token.", code="csrf_failed", status=400)
    return None


@developer_bp.get("/keys")
def keys_list():
    error = _require_session_user()
    if error:
        return error
    keys = list_api_keys(g.user.id)
    return api_success({"keys": [
        {
            "id": item.id,
            "name": item.name,
            "prefix": item.key_prefix,
            "created_at": item.created_at.isoformat(),
            "last_used_at": item.last_used_at.isoformat() if item.last_used_at else None,
            "revoked": item.revoked_at is not None,
        }
        for item in keys
    ]})


@developer_bp.post("/keys")
def keys_create():
    error = _require_session_user() or _require_csrf()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    record, raw_key = create_api_key(user_id=g.user.id, name=payload.get("name", "Default"))
    return api_success({
        "key": {
            "id": record.id,
            "name": record.name,
            "prefix": record.key_prefix,
            "secret": raw_key,
            "warning": "Copy this key now. AvatarForge stores only a hash and cannot show it again.",
        }
    }, status=201)


@developer_bp.delete("/keys/<key_id>")
def keys_revoke(key_id: str):
    error = _require_session_user() or _require_csrf()
    if error:
        return error
    if not revoke_api_key(user_id=g.user.id, key_id=key_id):
        return api_error("API key not found.", code="not_found", status=404)
    return api_success({"revoked": True})


@developer_bp.get("/usage")
def usage():
    error = _require_session_user()
    if error:
        return error
    items = []
    for key in list_api_keys(g.user.id):
        current = usage_for_key(key.id)
        quota, used, remaining = generation_quota_remaining(key.id)
        items.append({
            "api_key_id": key.id,
            "name": key.name,
            "prefix": key.key_prefix,
            "requests": current.request_count if current else 0,
            "generations": used,
            "generation_quota": quota,
            "remaining": remaining,
        })
    return api_success({"period": datetime.now(timezone.utc).strftime("%Y-%m"), "keys": items})
