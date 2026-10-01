from __future__ import annotations

import base64
import time

from pathlib import Path

from flask import Blueprint, current_app, g, request, send_file, url_for

from services.generation_service import generate_avatar
from services.history_service import save_generation
from services.job_service import can_access_job, create_generation_job, get_job
from services.queue_service import enqueue_generation_job
from services.image_service import STYLE_LABELS
from utils.api_response import api_error, api_success

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_v1_bp.get("/health")
def health():
    return api_success(
        {
            "service": "avatarforge-ai",
            "status": "ok",
            "version": "v1",
            "queue_backend": current_app.config.get("JOB_BACKEND", "thread"),
        }
    )


@api_v1_bp.get("/styles")
def styles():
    return api_success(
        [
            {"id": style_id, "label": label, "engine": "computer-vision"}
            for style_id, label in STYLE_LABELS.items()
        ],
        meta={"count": len(STYLE_LABELS)},
    )


@api_v1_bp.post("/generate")
def generate_v1():
    if "file" not in request.files:
        return api_error("No image was uploaded.", code="missing_file", status=400)

    started_at = time.perf_counter()

    try:
        result = generate_avatar(
            request.files.get("file"),
            request.form.get("style"),
            request.form.get("intensity"),
            request.form.get("engine"),
            request.form.get("prompt"),
        )
        image_bytes = result.image_stream.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode("ascii")
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

        saved_generation = None
        if g.get("user") is not None:
            saved_generation = save_generation(
                user_id=g.user.id,
                result=result,
                processing_ms=elapsed_ms,
            )

        generation_payload = {
            "style": result.style,
            "style_label": result.style_label,
            "intensity": result.intensity,
            "saved": saved_generation is not None,
            "engine": result.engine,
            "provider": result.provider,
            "prompt": result.prompt,
        }
        if saved_generation is not None:
            generation_payload.update(
                {
                    "id": saved_generation.id,
                    "history_url": url_for("account.generations"),
                    "image_url": url_for(
                        "account.generation_image", generation_id=saved_generation.id
                    ),
                }
            )

        return api_success(
            {
                "image": {
                    "mime_type": "image/jpeg",
                    "base64": image_base64,
                    "download_name": result.download_name,
                },
                "generation": generation_payload,
            },
            meta={"processing_ms": elapsed_ms},
        )
    except ValueError as exc:
        return api_error(str(exc), code="validation_error", status=400)
    except Exception:
        current_app.logger.exception("Avatar generation failed")
        return api_error(
            "We could not process that image. Please try another one.",
            code="generation_failed",
            status=500,
        )


@api_v1_bp.post("/jobs")
def create_job_v1():
    if "file" not in request.files:
        return api_error("No image was uploaded.", code="missing_file", status=400)

    try:
        job, access_token = create_generation_job(
            file_storage=request.files.get("file"),
            raw_style=request.form.get("style"),
            raw_intensity=request.form.get("intensity"),
            raw_engine=request.form.get("engine"),
            raw_prompt=request.form.get("prompt"),
            user_id=g.user.id if g.get("user") is not None else None,
        )
        backend = enqueue_generation_job(job.id)
        return api_success(
            {
                "job": {
                    "id": job.id,
                    "status": job.status,
                    "progress": job.progress,
                    "access_token": access_token,
                    "status_url": url_for("api_v1.job_status_v1", job_id=job.id),
                }
            },
            meta={"queue_backend": backend},
            status=202,
        )
    except ValueError as exc:
        return api_error(str(exc), code="validation_error", status=400)
    except Exception:
        current_app.logger.exception("Could not create generation job")
        return api_error("We could not queue that generation.", code="queue_failed", status=500)


def _job_token():
    return request.headers.get("X-Job-Token") or request.args.get("token")


@api_v1_bp.get("/jobs/<job_id>")
def job_status_v1(job_id):
    job = get_job(job_id)
    if job is None:
        return api_error("Generation job not found.", code="job_not_found", status=404)

    user_id = g.user.id if g.get("user") is not None else None
    if not can_access_job(job, user_id=user_id, token=_job_token()):
        return api_error("You do not have access to this job.", code="forbidden", status=403)

    payload = {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "style": job.style,
        "intensity": job.intensity,
        "engine": job.engine,
        "provider": job.provider,
        "processing_ms": job.processing_ms,
        "saved": bool(job.generation_id),
        "error": job.error_message if job.status == "failed" else None,
    }
    if job.status == "completed":
        payload["image_url"] = url_for("api_v1.job_image_v1", job_id=job.id)
        payload["download_name"] = job.download_name or "avatarforge-result.jpg"
        if job.generation_id:
            payload["generation_id"] = job.generation_id
            payload["history_url"] = url_for("account.generations")

    return api_success({"job": payload})


@api_v1_bp.get("/jobs/<job_id>/image")
def job_image_v1(job_id):
    job = get_job(job_id)
    if job is None:
        return api_error("Generation job not found.", code="job_not_found", status=404)

    user_id = g.user.id if g.get("user") is not None else None
    if not can_access_job(job, user_id=user_id, token=_job_token()):
        return api_error("You do not have access to this job.", code="forbidden", status=403)
    if job.status != "completed" or not job.output_path:
        return api_error("Generation result is not ready yet.", code="job_not_ready", status=409)

    path = Path(job.output_path)
    if not path.is_file():
        return api_error("Generation result is unavailable.", code="result_missing", status=404)
    return send_file(
        path,
        mimetype=job.output_mime_type or "image/jpeg",
        as_attachment=False,
        download_name=job.download_name or "avatarforge-result.jpg",
    )
