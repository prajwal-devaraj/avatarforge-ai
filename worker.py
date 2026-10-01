"""RQ worker entry point for AvatarForge AI generation jobs."""
from app import app
from services.job_service import process_generation_job


def run_generation_job(job_id: str) -> None:
    with app.app_context():
        process_generation_job(job_id)
