"""Legacy compatibility routes.

The browser app now uses /api/v1. This route remains temporarily available so
older clients do not break while the API migrates.
"""

from flask import Blueprint, current_app, jsonify, request, send_file

from services.generation_service import generate_avatar

api_bp = Blueprint("api", __name__)


@api_bp.post("/generate")
def generate():
    if "file" not in request.files:
        return jsonify({"error": "No image was uploaded."}), 400

    try:
        result = generate_avatar(
            request.files.get("file"),
            request.form.get("style"),
            request.form.get("intensity"),
        )
        return send_file(
            result.image_stream,
            mimetype="image/jpeg",
            download_name=result.download_name,
            headers={
                "X-AvatarForge-Style": result.style,
                "X-AvatarForge-Style-Label": result.style_label,
                "X-AvatarForge-Intensity": str(result.intensity),
                "Deprecation": "true",
                "Link": '</api/v1/generate>; rel="successor-version"',
            },
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Avatar generation failed")
        return jsonify({"error": "We could not process that image. Please try another one."}), 500
