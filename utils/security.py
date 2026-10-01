from __future__ import annotations

import secrets

from flask import session


def csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def valid_csrf_token(candidate: str | None) -> bool:
    expected = session.get("csrf_token")
    return bool(expected and candidate and secrets.compare_digest(expected, candidate))
