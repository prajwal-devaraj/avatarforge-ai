from __future__ import annotations

from pathlib import Path

from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from models import Base


def init_database(app: Flask) -> None:
    """Create the SQLAlchemy engine/session factory and initialize tables."""
    database_url = app.config["DATABASE_URL"]

    if database_url.startswith("sqlite:///"):
        raw_path = database_url.removeprefix("sqlite:///")
        Path(raw_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(database_url, future=True, pool_pre_ping=True)
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
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = session_factory

    @app.teardown_appcontext
    def remove_database_session(_error=None):
        session_factory.remove()
