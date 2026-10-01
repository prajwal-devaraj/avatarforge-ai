from pathlib import Path

from app import create_app
from config import Config
from services.storage_service import delete_location, location_exists, read_bytes, store_bytes


class StorageTestConfig(Config):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    STORAGE_BACKEND = "local"


def test_local_storage_round_trip(tmp_path):
    class TempConfig(StorageTestConfig):
        GENERATED_STORAGE_DIR = str(tmp_path / "generated")
        JOB_STORAGE_DIR = str(tmp_path / "jobs")

    app = create_app(TempConfig)
    with app.app_context():
        location = store_bytes(
            category="generations",
            key="user-1/avatar.jpg",
            data=b"avatar-bytes",
            mime_type="image/jpeg",
        )
        assert Path(location).is_file()
        assert location_exists(location) is True
        assert read_bytes(location) == b"avatar-bytes"
        assert delete_location(location) is True
        assert location_exists(location) is False


def test_readiness_and_metrics_endpoints(tmp_path):
    class TempConfig(StorageTestConfig):
        GENERATED_STORAGE_DIR = str(tmp_path / "generated")
        JOB_STORAGE_DIR = str(tmp_path / "jobs")

    client = create_app(TempConfig).test_client()
    readiness = client.get("/api/v1/ready")
    payload = readiness.get_json()
    assert readiness.status_code == 200
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["checks"]["database"] == "ok"
    assert payload["data"]["checks"]["storage"] == "local"

    metrics = client.get("/api/v1/metrics")
    assert metrics.status_code == 200
    assert b"avatarforge_http_requests_total" in metrics.data
