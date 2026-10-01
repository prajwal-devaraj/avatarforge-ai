from __future__ import annotations

from io import BytesIO

from flask import Blueprint, abort, g, render_template, request, send_file

from services.history_service import get_owned_generation, list_generations
from services.storage_service import location_exists, read_bytes
from utils.auth import login_required


account_bp = Blueprint("account", __name__)


@account_bp.get("/generations")
@login_required
def generations():
    items = list_generations(g.user.id)
    return render_template("generations.html", generations=items)


@account_bp.get("/generations/<generation_id>/image")
@login_required
def generation_image(generation_id: str):
    generation = get_owned_generation(generation_id, g.user.id)
    if generation is None:
        abort(404)

    if not location_exists(generation.output_path):
        abort(404)

    as_attachment = request.args.get("download") == "1"
    download_name = f"avatarforge-{generation.style}-{generation.id[:8]}.jpg"
    return send_file(
        BytesIO(read_bytes(generation.output_path)),
        mimetype=generation.mime_type,
        as_attachment=as_attachment,
        download_name=download_name,
        conditional=True,
    )
