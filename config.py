import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_SQLITE_PATH = INSTANCE_DIR / "avatarforge.db"


def normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://") and "+" not in value.split("://", 1)[0]:
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


class Config:
    """Base application configuration for AvatarForge AI."""

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    JSON_SORT_KEYS = False
    SECRET_KEY = os.environ.get("AVATARFORGE_SECRET_KEY", "dev-only-change-me")
    DATABASE_URL = normalize_database_url(
        os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")
    )
    GENERATED_STORAGE_DIR = os.environ.get(
        "AVATARFORGE_GENERATED_DIR", str(INSTANCE_DIR / "generated")
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 14
    AUTO_CREATE_DB = True
    AI_PROVIDER = os.environ.get("AVATARFORGE_AI_PROVIDER", "remote")
    AI_ENDPOINT = os.environ.get("AVATARFORGE_AI_ENDPOINT", "")
    AI_API_KEY = os.environ.get("AVATARFORGE_AI_API_KEY", "")
    AI_TIMEOUT = int(os.environ.get("AVATARFORGE_AI_TIMEOUT", "120"))
    FAL_KEY = os.environ.get("FAL_KEY", "")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    AUTO_CREATE_DB = False
