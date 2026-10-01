from io import BytesIO

from PIL import Image

from app import create_app
from config import Config


class DevApiConfig(Config):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    GENERATED_STORAGE_DIR = "/tmp/avatarforge-dev-api-generated"
    JOB_STORAGE_DIR = "/tmp/avatarforge-dev-api-jobs"
    SECRET_KEY = "test-secret"
    AI_PROVIDER = "mock"
    JOB_BACKEND = "inline"
    API_MONTHLY_GENERATION_QUOTA = 2
    API_RATE_LIMIT_PER_MINUTE = 100
    RATE_LIMIT_BACKEND = "memory"


def make_image_file():
    buffer = BytesIO()
    Image.new("RGB", (24, 24), (80, 120, 200)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def register(client):
    client.get("/auth/register")
    with client.session_transaction() as session:
        token = session["csrf_token"]
    response = client.post(
        "/auth/register",
        data={
            "_csrf": token,
            "email": "developer@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        token = session.get("csrf_token")
    return token


def test_create_list_and_revoke_api_key():
    client = create_app(DevApiConfig).test_client()
    csrf = register(client)

    created = client.post(
        "/api/v1/developer/keys",
        json={"name": "Local CLI"},
        headers={"X-CSRF-Token": csrf},
    )
    payload = created.get_json()
    assert created.status_code == 201
    assert payload["data"]["key"]["secret"].startswith("af_live_")
    key_id = payload["data"]["key"]["id"]

    listed = client.get("/api/v1/developer/keys").get_json()
    assert listed["data"]["keys"][0]["name"] == "Local CLI"
    assert "secret" not in listed["data"]["keys"][0]

    revoked = client.delete(
        f"/api/v1/developer/keys/{key_id}",
        headers={"X-CSRF-Token": csrf},
    )
    assert revoked.status_code == 200


def test_api_key_tracks_usage_and_enforces_quota():
    client = create_app(DevApiConfig).test_client()
    csrf = register(client)
    raw_key = client.post(
        "/api/v1/developer/keys",
        json={"name": "Quota Test"},
        headers={"X-CSRF-Token": csrf},
    ).get_json()["data"]["key"]["secret"]

    headers = {"Authorization": f"Bearer {raw_key}"}
    for _ in range(2):
        response = client.post(
            "/api/v1/generate",
            data={"file": (make_image_file(), "avatar.png"), "style": "cartoon", "intensity": "70"},
            headers=headers,
            content_type="multipart/form-data",
        )
        assert response.status_code == 200

    blocked = client.post(
        "/api/v1/generate",
        data={"file": (make_image_file(), "avatar.png"), "style": "cartoon", "intensity": "70"},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert blocked.status_code == 429
    assert blocked.get_json()["error"]["code"] == "quota_exceeded"

    usage = client.get("/api/v1/developer/usage").get_json()["data"]["keys"][0]
    assert usage["generations"] == 2
    assert usage["remaining"] == 0
