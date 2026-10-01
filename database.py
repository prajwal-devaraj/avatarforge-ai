from __future__ import annotations

from pathlib import Path

from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from models import Base


def init_database(app: Flask) -> None:
    """Create the SQLAlchemy engine/session factory and initialize tables."""
    database_url = app.config["DATABASE_URL"]

    if (
        app.config.get("DEBUG") is False
        and not app.config.get("TESTING", False)
        and app.config.get("REQUIRE_POSTGRES_IN_PRODUCTION", True)
        and database_url.startswith("sqlite")
    ):
        raise RuntimeError("Production requires PostgreSQL. Set DATABASE_URL to a PostgreSQL database.")

    if database_url.startswith("sqlite:///"):
        raw_path = database_url.removeprefix("sqlite:///")
        Path(raw_path).parent.mkdir(parents=True, exist_ok=True)

    engine_options = {"future": True, "pool_pre_ping": True}
    if database_url.startswith("postgresql"):
        if str(app.config.get("DB_POOL_MODE", "pooled")).lower() == "serverless":
            engine_options["poolclass"] = NullPool
        else:
            engine_options.update({"pool_recycle": 300, "pool_size": 5, "max_overflow": 10})
    engine = create_engine(database_url, **engine_options)
    session_factory = scoped_session(
        sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    )

    if app.config.get("AUTO_CREATE_DB", True):
        Base.metadata.create_all(engine)
        # Development compatibility for SQLite databases created before retry metadata existed.
        # Production deployments use Alembic migrations instead.
        if database_url.startswith("sqlite:///"):
            with engine.begin() as connection:
                columns = {row[1] for row in connection.execute(text("PRAGMA table_info(generation_jobs)"))}
                if columns and "attempt_count" not in columns:
                    connection.execute(text("ALTER TABLE generation_jobs ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0"))
                if columns and "max_attempts" not in columns:
                    connection.execute(text("ALTER TABLE generation_jobs ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 2"))
            with engine.begin() as connection:
                user_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(users)"))}
                if user_columns and "email_verified_at" not in user_columns:
                    connection.execute(text("ALTER TABLE users ADD COLUMN email_verified_at DATETIME"))
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = session_factory

    @app.teardown_appcontext
    def remove_database_session(error=None):
        if error is not None:
            session_factory.rollback()
        session_factory.remove()
