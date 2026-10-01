from io import BytesIO

from werkzeug.datastructures import FileStorage

from app import create_app
from config import Config
from services.job_service import create_generation_job
from services.storage_service import read_bytes


class VercelLikeTestConfig(Config):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "vercel-test-secret"
    DATABASE_URL = "sqlite:///:memory:"
    REQUIRE_POSTGRES_IN_PRODUCTION = True
    AUTO_CREATE_DB = True
    JOB_BACKEND = "inline"
    STORAGE_BACKEND = "local"
    GENERATED_STORAGE_DIR = "/tmp/avatarforge-vercel-test-generated"
    JOB_STORAGE_DIR = "/tmp/avatarforge-vercel-test-jobs"


def test_testing_mode_can_use_sqlite_with_production_debug_setting():
    app = create_app(VercelLikeTestConfig)
    assert app.config["TESTING"] is True


def test_job_input_uses_storage_abstraction(tmp_path):
    class TempConfig(VercelLikeTestConfig):
        DATABASE_URL = f"sqlite:///{(tmp_path / 'jobs.db').as_posix()}"
        JOB_STORAGE_DIR = str(tmp_path / "jobs")
        GENERATED_STORAGE_DIR = str(tmp_path / "generated")

    app = create_app(TempConfig)
    with app.app_context():
        upload = FileStorage(
            stream=BytesIO(b"avatar-input"),
            filename="avatar.png",
            content_type="image/png",
        )
        job, _token = create_generation_job(
            file_storage=upload,
            raw_style="cartoon",
            raw_intensity="50",
            raw_engine="classic",
            raw_prompt="",
        )
        assert read_bytes(job.input_path) == b"avatar-input"
