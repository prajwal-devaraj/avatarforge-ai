from __future__ import annotations

from typing import Any

from flask import g, jsonify


def api_success(data: Any = None, *, meta: dict | None = None, status: int = 200):
    payload = {
        "success": True,
        "data": data,
        "error": None,
        "meta": {"request_id": getattr(g, "request_id", None), **(meta or {})},
    }
    return jsonify(payload), status


def api_error(message: str, *, code: str = "bad_request", status: int = 400, details: Any = None):
    payload = {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": {"request_id": getattr(g, "request_id", None)},
    }
    return jsonify(payload), status
