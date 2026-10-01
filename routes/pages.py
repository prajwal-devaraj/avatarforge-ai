from flask import Blueprint, render_template

from services.image_service import STYLE_LABELS


pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def index():
    return render_template("index.html")


@pages_bp.get("/studio")
def studio():
    return render_template("studio.html", styles=STYLE_LABELS)
