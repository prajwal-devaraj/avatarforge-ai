from __future__ import annotations

from datetime import datetime, timezone

from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select

from models import User
from services.email_service import send_email


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def create_email_verification_token(user: User) -> str:
    return _serializer().dumps(
        {"purpose": "verify-email", "user_id": user.id, "email": user.email},
        salt="avatarforge-email-verification",
    )


def create_password_reset_token(user: User) -> str:
    # password_hash is included so any password change invalidates old reset links.
    return _serializer().dumps(
        {
            "purpose": "password-reset",
            "user_id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
        },
        salt="avatarforge-password-reset",
    )


def _load_token(token: str, *, salt: str, max_age: int) -> dict | None:
    try:
        payload = _serializer().loads(token, salt=salt, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    return payload if isinstance(payload, dict) else None


def verify_email_token(token: str) -> User | None:
    payload = _load_token(
        token,
        salt="avatarforge-email-verification",
        max_age=int(current_app.config["EMAIL_VERIFICATION_TOKEN_MAX_AGE"]),
    )
    if not payload or payload.get("purpose") != "verify-email":
        return None

    db = current_app.extensions["db_session"]
    user = db.scalar(select(User).where(User.id == payload.get("user_id")))
    if user is None or user.email != payload.get("email"):
        return None

    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()
    return user


def resolve_password_reset_token(token: str) -> User | None:
    payload = _load_token(
        token,
        salt="avatarforge-password-reset",
        max_age=int(current_app.config["PASSWORD_RESET_TOKEN_MAX_AGE"]),
    )
    if not payload or payload.get("purpose") != "password-reset":
        return None

    db = current_app.extensions["db_session"]
    user = db.scalar(select(User).where(User.id == payload.get("user_id")))
    if user is None:
        return None
    if user.email != payload.get("email") or user.password_hash != payload.get("password_hash"):
        return None
    return user


def send_verification_email(user: User) -> None:
    token = create_email_verification_token(user)
    link = url_for("auth.verify_email", token=token, _external=True)
    send_email(
        to=user.email,
        subject="Verify your AvatarForge AI email",
        text=f"Verify your AvatarForge AI email by opening this link:\n\n{link}\n\nIf you did not create this account, ignore this email.",
    )


def send_password_reset_email(user: User) -> None:
    token = create_password_reset_token(user)
    link = url_for("auth.reset_password", token=token, _external=True)
    send_email(
        to=user.email,
        subject="Reset your AvatarForge AI password",
        text=f"Reset your AvatarForge AI password by opening this link:\n\n{link}\n\nIf you did not request a reset, ignore this email.",
    )
