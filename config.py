import os


class Config:
    """Base application configuration for AvatarForge AI."""

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    JSON_SORT_KEYS = False
    SECRET_KEY = os.environ.get("AVATARFORGE_SECRET_KEY", "dev-only-change-me")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
