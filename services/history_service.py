from __future__ import annotations

from pathlib import Path

from flask import current_app
from sqlalchemy import select

from models import Generation


def save_generation(*, user_id: str, result, processing_ms: float) -> Generation:
    """Persist a generated image and its metadata for the signed-in user."""
    generation = Generation(
        user_id=user_id,
        style=result.style,
        style_label=result.style_label,
        intensity=result.intensity,
        output_path="",
        mime_type="image/jpeg",
        processing_ms=processing_ms,
    )

    user_dir = Path(current_app.config["GENERATED_STORAGE_DIR"]) / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_dir / f"{generation.id}.jpg"
    file_path.write_bytes(result.image_stream.getvalue())
    generation.output_path = str(file_path)

    db = current_app.extensions["db_session"]
    db.add(generation)
    db.commit()
    return generation


def list_generations(user_id: str) -> list[Generation]:
    db = current_app.extensions["db_session"]
    statement = (
        select(Generation)
        .where(Generation.user_id == user_id)
        .order_by(Generation.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_owned_generation(generation_id: str, user_id: str) -> Generation | None:
    db = current_app.extensions["db_session"]
    statement = select(Generation).where(
        Generation.id == generation_id,
        Generation.user_id == user_id,
    )
    return db.scalar(statement)
