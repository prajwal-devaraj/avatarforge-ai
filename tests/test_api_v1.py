from io import BytesIO

from PIL import Image

from app import create_app
from config import Config


class TestConfig(Config):
    TESTING = True


def make_image_file():
    buffer = BytesIO()
    Image.new("RGB", (24, 24), (120, 80, 200)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_health_contract():
    client = create_app(TestConfig).test_client()
    response = client.get("/api/v1/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["meta"]["request_id"]
    assert response.headers["X-Request-ID"] == payload["meta"]["request_id"]


def test_styles_contract():
    client = create_app(TestConfig).test_client()
    response = client.get("/api/v1/styles")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["meta"]["count"] == 6
    assert any(style["id"] == "cartoon" for style in payload["data"])


def test_generate_requires_file_v1():
    client = create_app(TestConfig).test_client()
    response = client.post("/api/v1/generate", data={})
    payload = response.get_json()
    assert response.status_code == 400
    assert payload["success"] is False
    assert payload["error"]["code"] == "missing_file"


def test_generate_returns_json_image_contract():
    client = create_app(TestConfig).test_client()
    response = client.post(
        "/api/v1/generate",
        data={
            "file": (make_image_file(), "avatar.png"),
            "style": "grayscale",
            "intensity": "65",
        },
        content_type="multipart/form-data",
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["image"]["mime_type"] == "image/jpeg"
    assert payload["data"]["image"]["base64"]
    assert payload["data"]["generation"]["style"] == "grayscale"
    assert payload["data"]["generation"]["intensity"] == 65
    assert payload["meta"]["processing_ms"] >= 0


def test_request_id_can_be_provided_by_client():
    client = create_app(TestConfig).test_client()
    response = client.get("/api/v1/health", headers={"X-Request-ID": "client-request-123"})
    payload = response.get_json()
    assert payload["meta"]["request_id"] == "client-request-123"
    assert response.headers["X-Request-ID"] == "client-request-123"
