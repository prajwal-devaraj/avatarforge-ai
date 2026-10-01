from __future__ import annotations

import base64
import time

from flask import Blueprint, current_app, g, request, url_for

from services.generation_service import generate_avatar
from services.history_service import save_generation
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
