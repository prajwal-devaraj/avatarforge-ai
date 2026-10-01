from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from flask import current_app

_local_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="avatarforge-job")


def enqueue_generation_job(job_id: str) -> str:
    """Queue a generation job using inline, local-thread, or Redis/RQ execution."""
    backend = current_app.config.get("JOB_BACKEND", "thread").lower()
    app = current_app._get_current_object()

    if backend == "inline":
        from services.job_service import process_generation_job

        process_generation_job(job_id)
        return "inline"

    if backend == "rq":
        try:
            from redis import Redis
            from rq import Queue
        except ImportError as exc:
            raise RuntimeError("Redis/RQ dependencies are not installed.") from exc

        redis_conn = Redis.from_url(current_app.config["REDIS_URL"])
        queue = Queue(current_app.config.get("RQ_QUEUE", "avatarforge"), connection=redis_conn)
        queue.enqueue("worker.run_generation_job", job_id, job_timeout=current_app.config.get("JOB_TIMEOUT", 300))
        return "rq"

    if backend != "thread":
        raise RuntimeError(f"Unsupported job backend: {backend}")

    def runner():
        from services.job_service import process_generation_job

        with app.app_context():
            process_generation_job(job_id)

    _local_executor.submit(runner)
    return "thread"
