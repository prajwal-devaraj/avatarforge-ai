from __future__ import annotations

from flask import current_app
from sqlalchemy import select

from models import Generation
from services.storage_service import store_bytes


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

    db = current_app.extensions["db_session"]
    db.add(generation)
    db.flush()

    generation.output_path = store_bytes(
        category="generations",
        key=f"{user_id}/{generation.id}.jpg",
        data=result.image_stream.getvalue(),
        mime_type="image/jpeg",
    )
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
