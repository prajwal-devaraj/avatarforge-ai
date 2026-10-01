from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import current_app
from sqlalchemy import delete, select

from models import GenerationJob
from services.storage_service import delete_location


def cleanup_expired_jobs(*, older_than_hours: int | None = None) -> dict:
    """Delete old terminal job artifacts and database rows.

    Saved user generations are never removed by this cleanup routine.
    """
    ttl = older_than_hours or int(current_app.config.get("JOB_RETENTION_HOURS", 24))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl)
    db = current_app.extensions["db_session"]
    jobs = list(
        db.scalars(
            select(GenerationJob).where(
                GenerationJob.status.in_(("completed", "failed")),
                GenerationJob.completed_at.is_not(None),
                GenerationJob.completed_at < cutoff,
            )
        ).all()
    )
    deleted_artifacts = 0
    for job in jobs:
        if delete_location(job.output_path):
            deleted_artifacts += 1
        try:
            job_dir = Path(current_app.config["JOB_STORAGE_DIR"]) / job.id
            if job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)
        except OSError:
            current_app.logger.warning("Could not remove job directory for %s", job.id)
        db.delete(job)
    db.commit()
    return {"jobs_deleted": len(jobs), "artifacts_deleted": deleted_artifacts, "retention_hours": ttl}
