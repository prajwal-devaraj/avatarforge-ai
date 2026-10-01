from __future__ import annotations

from functools import wraps
from urllib.parse import urljoin, urlparse

from flask import g, redirect, request, session, url_for

from utils.security import csrf_token


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)

    return wrapped


def is_safe_next_url(target: str | None) -> bool:
    if not target:
        return False
    host_url = request.host_url
    reference = urlparse(host_url)
    candidate = urlparse(urljoin(host_url, target))
    return candidate.scheme in {"http", "https"} and reference.netloc == candidate.netloc


def sign_in_user(user_id: str) -> None:
    session.clear()
    session["user_id"] = user_id
    session.permanent = True
    csrf_token()


def sign_out_user() -> None:
    session.clear()

