from __future__ import annotations

import re

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import User
from utils.auth import is_safe_next_url, sign_in_user, sign_out_user
from utils.security import valid_csrf_token


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


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

        if not EMAIL_RE.match(email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
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
        else:
            sign_in_user(user.id)
            if is_safe_next_url(next_url):
                return redirect(next_url)
            return redirect(url_for("pages.studio"))

    return render_template("auth/login.html", next_url=next_url or "")


@auth_bp.post("/logout")
def logout():
    if not valid_csrf_token(request.form.get("_csrf")):
        return redirect(url_for("pages.index"))
    sign_out_user()
    return redirect(url_for("pages.index"))
