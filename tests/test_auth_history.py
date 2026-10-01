from io import BytesIO
from pathlib import Path

from PIL import Image

from app import create_app
from config import Config


class TestConfig(Config):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    GENERATED_STORAGE_DIR = "/tmp/avatarforge-test-generated"
    SECRET_KEY = "test-secret"


def make_image_file():
    buffer = BytesIO()
    Image.new("RGB", (24, 24), (100, 150, 210)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def csrf_for(client, path="/auth/register"):
    client.get(path)
    with client.session_transaction() as session:
        return session["csrf_token"]


def register(client, email="creator@example.com"):
    token = csrf_for(client)
    return client.post(
        "/auth/register",
        data={
            "_csrf": token,
            "email": email,
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )


def test_register_login_and_logout_flow():
    app = create_app(TestConfig)
    client = app.test_client()

    response = register(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/studio")

    history = client.get("/generations")
    assert history.status_code == 200
    assert b"creator@example.com" in history.data

    with client.session_transaction() as session:
        token = session.get("csrf_token")
    if not token:
        token = csrf_for(client, "/studio")
    logout = client.post("/auth/logout", data={"_csrf": token})
    assert logout.status_code == 302

    protected = client.get("/generations")
    assert protected.status_code == 302
    assert "/auth/login" in protected.headers["Location"]


def test_signed_in_generation_is_saved_to_private_history(tmp_path):
    class TempConfig(TestConfig):
        DATABASE_URL = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
        GENERATED_STORAGE_DIR = str(tmp_path / "generated")

    app = create_app(TempConfig)
    client = app.test_client()
    register(client)

    response = client.post(
        "/api/v1/generate",
        data={
            "file": (make_image_file(), "avatar.png"),
            "style": "cartoon",
            "intensity": "70",
        },
        content_type="multipart/form-data",
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["data"]["generation"]["saved"] is True
    generation_id = payload["data"]["generation"]["id"]

    history = client.get("/generations")
    assert history.status_code == 200
    assert b"Signature Cartoon" in history.data

    image_response = client.get(f"/generations/{generation_id}/image")
    assert image_response.status_code == 200
    assert image_response.mimetype == "image/jpeg"

    files = list(Path(TempConfig.GENERATED_STORAGE_DIR).rglob("*.jpg"))
    assert len(files) == 1


def test_guest_generation_is_not_persisted(tmp_path):
    class TempConfig(TestConfig):
        DATABASE_URL = f"sqlite:///{(tmp_path / 'guest.db').as_posix()}"
        GENERATED_STORAGE_DIR = str(tmp_path / "guest-generated")

    client = create_app(TempConfig).test_client()
    response = client.post(
        "/api/v1/generate",
        data={"file": (make_image_file(), "avatar.png"), "style": "sketch", "intensity": "60"},
        content_type="multipart/form-data",
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["data"]["generation"]["saved"] is False
    assert not Path(TempConfig.GENERATED_STORAGE_DIR).exists()
