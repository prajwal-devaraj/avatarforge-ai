from __future__ import annotations

import re

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import User
from services.account_security_service import (
    resolve_password_reset_token,
    send_password_reset_email,
    send_verification_email,
    verify_email_token,
)
from utils.auth import is_safe_next_url, sign_in_user, sign_out_user
from utils.security import valid_csrf_token


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _valid_password(password: str) -> bool:
    return len(password) >= 8 and len(password) <= 128


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.get("user") is not None:
        return redirect(url_for("pages.studio"))

    if request.method == "POST":
        if not valid_csrf_token(request.form.get("_csrf")):
            flash("Your session token expired. Please try again.", "error")
            return render_template("auth/register.html"), 400

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not EMAIL_RE.match(email) or len(email) > 320:
            flash("Enter a valid email address.", "error")
        elif not _valid_password(password):
            flash("Password must be between 8 and 128 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            db = current_app.extensions["db_session"]
            user = User(email=email, password_hash="")
            user.set_password(password)
            db.add(user)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                flash("An account with that email already exists.", "error")
            else:
                if current_app.config.get("EMAIL_VERIFICATION_REQUIRED"):
                    send_verification_email(user)
                    flash("Account created. Check your email to verify your address before signing in.", "success")
                    return redirect(url_for("auth.login"))
                sign_in_user(user.id)
                return redirect(url_for("pages.studio"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.get("user") is not None:
        return redirect(url_for("pages.studio"))

    next_url = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        if not valid_csrf_token(request.form.get("_csrf")):
            flash("Your session token expired. Please try again.", "error")
            return render_template("auth/login.html", next_url=next_url or ""), 400

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = current_app.extensions["db_session"]
        user = db.scalar(select(User).where(User.email == email))

        if user is None or not user.check_password(password):
            flash("Email or password is incorrect.", "error")
        elif current_app.config.get("EMAIL_VERIFICATION_REQUIRED") and user.email_verified_at is None:
            flash("Verify your email address before signing in.", "error")
        else:
            sign_in_user(user.id)
            if is_safe_next_url(next_url):
                return redirect(next_url)
            return redirect(url_for("pages.studio"))

    return render_template("auth/login.html", next_url=next_url or "")


@auth_bp.get("/verify-email/<token>")
def verify_email(token: str):
    user = verify_email_token(token)
    if user is None:
        flash("That verification link is invalid or has expired.", "error")
        return redirect(url_for("auth.login"))
    flash("Email verified. You can now sign in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if request.method == "POST":
        if not valid_csrf_token(request.form.get("_csrf")):
            return render_template("auth/resend_verification.html"), 400
        email = request.form.get("email", "").strip().lower()
        db = current_app.extensions["db_session"]
        user = db.scalar(select(User).where(User.email == email))
        # Always show the same response to avoid account enumeration.
        if user is not None and user.email_verified_at is None:
            send_verification_email(user)
        flash("If that account exists and still needs verification, a new link has been sent.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/resend_verification.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        if not valid_csrf_token(request.form.get("_csrf")):
            return render_template("auth/forgot_password.html"), 400
        email = request.form.get("email", "").strip().lower()
        db = current_app.extensions["db_session"]
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            send_password_reset_email(user)
        flash("If an account exists for that email, a password reset link has been sent.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    user = resolve_password_reset_token(token)
    if user is None:
        flash("That password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        if not valid_csrf_token(request.form.get("_csrf")):
            return render_template("auth/reset_password.html", token=token), 400
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not _valid_password(password):
            flash("Password must be between 8 and 128 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            user.set_password(password)
            current_app.extensions["db_session"].commit()
            sign_out_user()
            flash("Password updated. Sign in with your new password.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.post("/logout")
def logout():
    if not valid_csrf_token(request.form.get("_csrf")):
        return redirect(url_for("pages.index"))
    sign_out_user()
    return redirect(url_for("pages.index"))
