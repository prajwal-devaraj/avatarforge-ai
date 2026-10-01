from app import create_app
from config import Config


class TestConfig(Config):
    TESTING = True


def test_homepage_loads():
    client = create_app(TestConfig).test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_studio_loads():
    client = create_app(TestConfig).test_client()
    response = client.get("/studio")
    assert response.status_code == 200


def test_legacy_generate_requires_file():
    client = create_app(TestConfig).test_client()
    response = client.post("/generate", data={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "No image was uploaded."
