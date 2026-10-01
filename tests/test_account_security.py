from sqlalchemy import select

from app import create_app
from config import Config
from models import User


class SecurityConfig(Config):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    GENERATED_STORAGE_DIR = "/tmp/avatarforge-security-generated"
    JOB_STORAGE_DIR = "/tmp/avatarforge-security-jobs"
    SECRET_KEY = "security-test-secret"
    EMAIL_BACKEND = "console"
    EMAIL_VERIFICATION_REQUIRED = True
    REQUIRE_POSTGRES_IN_PRODUCTION = False


def csrf_for(client, path):
    client.get(path)
    with client.session_transaction() as session:
        return session["csrf_token"]


def register_unverified(client):
    token = csrf_for(client, "/auth/register")
    return client.post(
        "/auth/register",
        data={
            "_csrf": token,
            "email": "secure@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )


def test_email_verification_required_before_login():
    app = create_app(SecurityConfig)
    client = app.test_client()
    response = register_unverified(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
    assert len(app.extensions["email_outbox"]) == 1

    login_csrf = csrf_for(client, "/auth/login")
    denied = client.post(
        "/auth/login",
        data={"_csrf": login_csrf, "email": "secure@example.com", "password": "password123"},
    )
    assert denied.status_code == 200
    assert b"Verify your email" in denied.data

    verification_url = app.extensions["email_outbox"][0]["text"].splitlines()[2]
    verified = client.get(verification_url)
    assert verified.status_code == 302

    with app.app_context():
        db = app.extensions["db_session"]
        user = db.scalar(select(User).where(User.email == "secure@example.com"))
        assert user.email_verified_at is not None

    login_csrf = csrf_for(client, "/auth/login")
    allowed = client.post(
        "/auth/login",
        data={"_csrf": login_csrf, "email": "secure@example.com", "password": "password123"},
    )
    assert allowed.status_code == 302
    assert allowed.headers["Location"].endswith("/studio")


def test_password_reset_changes_password_and_invalidates_token():
    class ResetConfig(SecurityConfig):
        EMAIL_VERIFICATION_REQUIRED = False

    app = create_app(ResetConfig)
    client = app.test_client()
    register_unverified(client)

    # Sign out registration session before testing the public recovery flow.
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    client.post("/auth/logout", data={"_csrf": csrf})

    reset_csrf = csrf_for(client, "/auth/forgot-password")
    requested = client.post(
        "/auth/forgot-password",
        data={"_csrf": reset_csrf, "email": "secure@example.com"},
    )
    assert requested.status_code == 302
    reset_url = app.extensions["email_outbox"][-1]["text"].splitlines()[2]

    page = client.get(reset_url)
    assert page.status_code == 200
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    changed = client.post(
        reset_url,
        data={"_csrf": csrf, "password": "newpassword123", "confirm_password": "newpassword123"},
    )
    assert changed.status_code == 302

    # The token embeds the old password hash and cannot be reused.
    reused = client.get(reset_url)
    assert reused.status_code == 302

    login_csrf = csrf_for(client, "/auth/login")
    login = client.post(
        "/auth/login",
        data={"_csrf": login_csrf, "email": "secure@example.com", "password": "newpassword123"},
    )
    assert login.status_code == 302


def test_security_headers_are_attached():
    app = create_app(SecurityConfig)
    response = app.test_client().get("/")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
