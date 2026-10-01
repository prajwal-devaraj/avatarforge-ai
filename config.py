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


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
    JOB_BACKEND = os.environ.get("AVATARFORGE_JOB_BACKEND", "thread")
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RQ_QUEUE = os.environ.get("AVATARFORGE_RQ_QUEUE", "avatarforge")
    JOB_TIMEOUT = int(os.environ.get("AVATARFORGE_JOB_TIMEOUT", "300"))
    JOB_STORAGE_DIR = os.environ.get(
        "AVATARFORGE_JOB_DIR", str(INSTANCE_DIR / "jobs")
    )
    TRUST_PROXY_HEADERS = env_bool("AVATARFORGE_TRUST_PROXY_HEADERS", False)
    STORAGE_BACKEND = os.environ.get("AVATARFORGE_STORAGE_BACKEND", "local")
    S3_BUCKET = os.environ.get("AVATARFORGE_S3_BUCKET", "")
    S3_PREFIX = os.environ.get("AVATARFORGE_S3_PREFIX", "avatarforge")
    S3_REGION = os.environ.get("AVATARFORGE_S3_REGION", "")
    S3_ENDPOINT_URL = os.environ.get("AVATARFORGE_S3_ENDPOINT_URL", "")
    S3_ACCESS_KEY_ID = os.environ.get("AVATARFORGE_S3_ACCESS_KEY_ID", "")
    S3_SECRET_ACCESS_KEY = os.environ.get("AVATARFORGE_S3_SECRET_ACCESS_KEY", "")
    S3_SERVER_SIDE_ENCRYPTION = os.environ.get("AVATARFORGE_S3_SSE", "AES256")
    JOB_MAX_ATTEMPTS = int(os.environ.get("AVATARFORGE_JOB_MAX_ATTEMPTS", "2"))
    JOB_RETENTION_HOURS = int(os.environ.get("AVATARFORGE_JOB_RETENTION_HOURS", "24"))
    JSON_LOGS = env_bool("AVATARFORGE_JSON_LOGS", False)
    LOG_LEVEL = os.environ.get("AVATARFORGE_LOG_LEVEL", "INFO")
    API_MONTHLY_GENERATION_QUOTA = int(os.environ.get("AVATARFORGE_API_MONTHLY_GENERATION_QUOTA", "25"))
    API_RATE_LIMIT_PER_MINUTE = int(os.environ.get("AVATARFORGE_API_RATE_LIMIT_PER_MINUTE", "30"))
    RATE_LIMIT_BACKEND = os.environ.get("AVATARFORGE_RATE_LIMIT_BACKEND", "memory")
    BILLING_PROVIDER = os.environ.get("AVATARFORGE_BILLING_PROVIDER", "mock")
    APP_BASE_URL = os.environ.get("AVATARFORGE_APP_BASE_URL", "http://127.0.0.1:5000")
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_PRO = os.environ.get("STRIPE_PRICE_PRO", "")
    STRIPE_PRICE_BUSINESS = os.environ.get("STRIPE_PRICE_BUSINESS", "")
    PLAN_FREE_GENERATION_QUOTA = int(os.environ.get("AVATARFORGE_PLAN_FREE_GENERATION_QUOTA", str(API_MONTHLY_GENERATION_QUOTA)))
    PLAN_FREE_RATE_LIMIT_PER_MINUTE = int(os.environ.get("AVATARFORGE_PLAN_FREE_RATE_LIMIT_PER_MINUTE", str(API_RATE_LIMIT_PER_MINUTE)))
    PLAN_PRO_GENERATION_QUOTA = int(os.environ.get("AVATARFORGE_PLAN_PRO_GENERATION_QUOTA", "500"))
    PLAN_PRO_RATE_LIMIT_PER_MINUTE = int(os.environ.get("AVATARFORGE_PLAN_PRO_RATE_LIMIT_PER_MINUTE", "60"))
    PLAN_BUSINESS_GENERATION_QUOTA = int(os.environ.get("AVATARFORGE_PLAN_BUSINESS_GENERATION_QUOTA", "2500"))
    PLAN_BUSINESS_RATE_LIMIT_PER_MINUTE = int(os.environ.get("AVATARFORGE_PLAN_BUSINESS_RATE_LIMIT_PER_MINUTE", "180"))
    EMAIL_BACKEND = os.environ.get("AVATARFORGE_EMAIL_BACKEND", "console")
    EMAIL_FROM = os.environ.get("AVATARFORGE_EMAIL_FROM", "no-reply@avatarforge.local")
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = env_bool("SMTP_USE_TLS", True)
    EMAIL_VERIFICATION_REQUIRED = env_bool("AVATARFORGE_EMAIL_VERIFICATION_REQUIRED", False)
    EMAIL_VERIFICATION_TOKEN_MAX_AGE = int(os.environ.get("AVATARFORGE_EMAIL_VERIFICATION_TOKEN_MAX_AGE", "86400"))
    PASSWORD_RESET_TOKEN_MAX_AGE = int(os.environ.get("AVATARFORGE_PASSWORD_RESET_TOKEN_MAX_AGE", "3600"))
    REQUIRE_POSTGRES_IN_PRODUCTION = env_bool("AVATARFORGE_REQUIRE_POSTGRES_IN_PRODUCTION", True)


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    EMAIL_VERIFICATION_REQUIRED = env_bool("AVATARFORGE_EMAIL_VERIFICATION_REQUIRED", True)
    SESSION_COOKIE_SECURE = env_bool("AVATARFORGE_SESSION_COOKIE_SECURE", True)
    AUTO_CREATE_DB = False
