from __future__ import annotations

import hashlib
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app
from sqlalchemy import select
from werkzeug.datastructures import FileStorage

from models import GenerationJob
from services.generation_service import generate_avatar
from services.history_service import save_generation
from services.image_service import STYLE_LABELS
from services.storage_service import delete_location, read_bytes, store_bytes
from utils.observability import ACTIVE_JOBS, GENERATION_JOBS, GENERATION_LATENCY, JOB_RETRIES
from utils.validators import clamp_intensity, validate_upload

TERMINAL_STATUSES = {"completed", "failed"}


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_generation_job(*, file_storage, raw_style, raw_intensity, raw_engine, raw_prompt, user_id=None):
    validate_upload(file_storage)
    style = (raw_style or "cartoon").strip().lower()
    if style not in STYLE_LABELS:
        raise ValueError("That style is not supported.")
    intensity = clamp_intensity(raw_intensity)
    engine = (raw_engine or "classic").strip().lower()
    if engine not in {"classic", "ai"}:
        raise ValueError("Generation mode must be classic or ai.")

    token = secrets.token_urlsafe(32)
    job = GenerationJob(
        user_id=user_id,
        access_token_hash=_token_hash(token),
        status="queued",
        progress=0,
        style=style,
        intensity=intensity,
        engine=engine,
        prompt=(raw_prompt or "").strip()[:2000],
        input_path="",
        input_name=file_storage.filename or "upload.jpg",
        input_mime_type=file_storage.mimetype or "application/octet-stream",
        max_attempts=max(1, int(current_app.config.get("JOB_MAX_ATTEMPTS", 2))),
    )

    db = current_app.extensions["db_session"]
    db.add(job)
    db.flush()

    suffix = Path(job.input_name).suffix.lower() or ".bin"
    input_bytes = file_storage.read()
    file_storage.stream.seek(0)
    job.input_path = store_bytes(
        category="jobs",
        key=f"{job.id}/input{suffix}",
        data=input_bytes,
        mime_type=job.input_mime_type,
    )

    db.commit()
    return job, token


def get_job(job_id: str) -> GenerationJob | None:
    db = current_app.extensions["db_session"]
    return db.scalar(select(GenerationJob).where(GenerationJob.id == job_id))


def can_access_job(job: GenerationJob, *, user_id: str | None, token: str | None) -> bool:
    if user_id and job.user_id and user_id == job.user_id:
        return True
    if not token:
        return False
    return secrets.compare_digest(job.access_token_hash, _token_hash(token))


def process_generation_job(job_id: str) -> None:
    db = current_app.extensions["db_session"]
    job = db.scalar(select(GenerationJob).where(GenerationJob.id == job_id))
    if job is None or job.status in TERMINAL_STATUSES:
        return

    started = time.perf_counter()
    job.attempt_count = int(job.attempt_count or 0) + 1
    job.status = "processing"
    job.progress = 15
    job.started_at = datetime.now(timezone.utc)
    db.commit()
    ACTIVE_JOBS.inc()

    try:
        from io import BytesIO

        input_bytes = read_bytes(job.input_path)
        upload = FileStorage(
            stream=BytesIO(input_bytes),
            filename=job.input_name,
            content_type=job.input_mime_type,
        )
        result = generate_avatar(
            upload,
            job.style,
            str(job.intensity),
            job.engine,
            job.prompt,
        )

        job.progress = 80
        db.commit()

        job.output_path = store_bytes(
            category="jobs",
            key=f"{job.id}/result.jpg",
            data=result.image_stream.getvalue(),
            mime_type="image/jpeg",
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        generation_id = None
        if job.user_id:
            saved = save_generation(user_id=job.user_id, result=result, processing_ms=elapsed_ms)
            generation_id = saved.id

        job.output_mime_type = "image/jpeg"
        job.download_name = result.download_name
        job.provider = result.provider
        job.generation_id = generation_id
        job.processing_ms = elapsed_ms
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        GENERATION_JOBS.labels("completed", job.engine, job.provider or "classic").inc()
        GENERATION_LATENCY.labels(job.engine, job.provider or "classic").observe(elapsed_ms / 1000.0)
    except Exception as exc:
        current_app.logger.exception("Generation job %s failed on attempt %s", job_id, job.attempt_count)
        job.error_message = str(exc)[:1000] or "Generation failed."
        if int(job.attempt_count or 0) < int(job.max_attempts or 1):
            job.status = "queued"
            job.progress = 0
            db.commit()
            JOB_RETRIES.labels(job.engine).inc()
            from services.queue_service import enqueue_generation_job
            enqueue_generation_job(job.id)
        else:
            job.status = "failed"
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            GENERATION_JOBS.labels("failed", job.engine, job.provider or "unknown").inc()
    finally:
        ACTIVE_JOBS.dec()
        if job.status in TERMINAL_STATUSES:
            if not delete_location(job.input_path):
                current_app.logger.warning("Could not delete temporary job input for %s", job_id)
