from app import create_app
from config import Config
from services.billing_service import get_plan_for_user


class BillingConfig(Config):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    GENERATED_STORAGE_DIR = "/tmp/avatarforge-billing-generated"
    JOB_STORAGE_DIR = "/tmp/avatarforge-billing-jobs"
    SECRET_KEY = "billing-test-secret"
    AI_PROVIDER = "mock"
    JOB_BACKEND = "inline"
    BILLING_PROVIDER = "mock"
    API_MONTHLY_GENERATION_QUOTA = 7
    API_RATE_LIMIT_PER_MINUTE = 9
    PLAN_FREE_GENERATION_QUOTA = 7
    PLAN_FREE_RATE_LIMIT_PER_MINUTE = 9
    PLAN_PRO_GENERATION_QUOTA = 500
    PLAN_PRO_RATE_LIMIT_PER_MINUTE = 60


def register(client):
    client.get("/auth/register")
    with client.session_transaction() as session:
        token = session["csrf_token"]
    response = client.post(
        "/auth/register",
        data={
            "_csrf": token,
            "email": "billing@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        return session["csrf_token"]


def test_billing_dashboard_creates_free_subscription():
    app = create_app(BillingConfig)
    client = app.test_client()
    register(client)
    response = client.get("/account/billing")
    assert response.status_code == 200
    assert b"Billing & usage" in response.data
    assert b"Free" in response.data
    with app.app_context():
        from flask import g
        # Read the signed-in user through the database directly.
        from models import User
        from sqlalchemy import select
        db = app.extensions["db_session"]
        user = db.scalar(select(User).where(User.email == "billing@example.com"))
        assert get_plan_for_user(user.id).generation_quota == 7


def test_mock_checkout_upgrades_to_pro():
    app = create_app(BillingConfig)
    client = app.test_client()
    csrf = register(client)
    response = client.post("/account/billing/checkout/pro", data={"_csrf": csrf})
    assert response.status_code == 302
    dashboard = client.get("/account/billing")
    assert b"Current plan" in dashboard.data
    assert b"500" in dashboard.data


def test_account_settings_updates_email_and_password():
    app = create_app(BillingConfig)
    client = app.test_client()
    csrf = register(client)
    response = client.post(
        "/account/settings",
        data={"_csrf": csrf, "action": "profile", "email": "new@example.com"},
    )
    assert response.status_code == 302
    page = client.get("/account/settings")
    assert b"new@example.com" in page.data

    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    changed = client.post(
        "/account/settings",
        data={
            "_csrf": csrf,
            "action": "password",
            "current_password": "password123",
            "new_password": "newpassword123",
        },
    )
    assert changed.status_code == 302


def test_stripe_webhook_rejects_unsigned_payload():
    client = create_app(BillingConfig).test_client()
    response = client.post("/api/v1/billing/webhook", data=b'{"type":"test"}', content_type="application/json")
    assert response.status_code == 400
