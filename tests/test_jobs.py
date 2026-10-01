from io import BytesIO
from pathlib import Path

from PIL import Image

from app import create_app
from config import Config


class JobTestConfig(Config):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    GENERATED_STORAGE_DIR = "/tmp/avatarforge-step10-generated"
    JOB_STORAGE_DIR = "/tmp/avatarforge-step10-jobs"
    SECRET_KEY = "test-secret"
    AI_PROVIDER = "mock"
    JOB_BACKEND = "inline"


def make_image_file():
    buffer = BytesIO()
    Image.new("RGB", (32, 32), (90, 130, 210)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_job_lifecycle_for_guest(tmp_path):
    class TempConfig(JobTestConfig):
        DATABASE_URL = f"sqlite:///{(tmp_path / 'jobs.db').as_posix()}"
        GENERATED_STORAGE_DIR = str(tmp_path / "generated")
        JOB_STORAGE_DIR = str(tmp_path / "jobs")

    client = create_app(TempConfig).test_client()
    created = client.post(
        "/api/v1/jobs",
        data={
            "file": (make_image_file(), "avatar.png"),
            "style": "cartoon",
            "intensity": "70",
            "engine": "classic",
        },
        content_type="multipart/form-data",
    )
    payload = created.get_json()
    assert created.status_code == 202
    assert payload["success"] is True
    assert payload["meta"]["queue_backend"] == "inline"

    job = payload["data"]["job"]
    token = job["access_token"]
    job_id = job["id"]

    denied = client.get(f"/api/v1/jobs/{job_id}")
    assert denied.status_code == 403

    status = client.get(f"/api/v1/jobs/{job_id}", headers={"X-Job-Token": token})
    status_payload = status.get_json()
    assert status.status_code == 200
    assert status_payload["data"]["job"]["status"] == "completed"
    assert status_payload["data"]["job"]["progress"] == 100
    assert status_payload["data"]["job"]["saved"] is False

    image = client.get(
        f"/api/v1/jobs/{job_id}/image",
        headers={"X-Job-Token": token},
    )
    assert image.status_code == 200
    assert image.mimetype == "image/jpeg"
    assert image.data
    assert not list(Path(TempConfig.GENERATED_STORAGE_DIR).rglob("*.jpg"))


def test_job_ai_mode_uses_provider_metadata(tmp_path):
    class TempConfig(JobTestConfig):
        DATABASE_URL = f"sqlite:///{(tmp_path / 'ai-jobs.db').as_posix()}"
        GENERATED_STORAGE_DIR = str(tmp_path / "generated")
        JOB_STORAGE_DIR = str(tmp_path / "jobs")

    client = create_app(TempConfig).test_client()
    created = client.post(
        "/api/v1/jobs",
        data={
            "file": (make_image_file(), "avatar.png"),
            "style": "portrait",
            "intensity": "75",
            "engine": "ai",
            "prompt": "confident technology founder portrait",
        },
        content_type="multipart/form-data",
    )
    job = created.get_json()["data"]["job"]
    status = client.get(
        f"/api/v1/jobs/{job['id']}",
        headers={"X-Job-Token": job["access_token"]},
    ).get_json()["data"]["job"]
    assert status["status"] == "completed"
    assert status["engine"] == "ai"
    assert status["provider"] == "mock"
