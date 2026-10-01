import os
import uuid
from pathlib import Path

from flask import Flask, g, request, session
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import select

from config import DevelopmentConfig, ProductionConfig
from database import init_database
from models import User
from routes.account import account_bp
from routes.api import api_bp
from routes.api_v1 import api_v1_bp
from routes.auth import auth_bp
from routes.pages import pages_bp
from utils.api_response import api_error
from utils.security import csrf_token
from utils.observability import configure_json_logging, mark_request_start, observe_response


def create_app(config_object=None) -> Flask:
    """Application factory for the AvatarForge AI web application."""
    app = Flask(__name__)

    if config_object is None:
        environment = os.environ.get("AVATARFORGE_ENV", "development").lower()
        config_object = ProductionConfig if environment == "production" else DevelopmentConfig

    app.config.from_object(config_object)

    if app.config.get("TRUST_PROXY_HEADERS"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    if app.config.get("DEBUG") is False and app.config.get("SECRET_KEY") == "dev-only-change-me":
        raise RuntimeError("AVATARFORGE_SECRET_KEY must be set in production.")

    init_database(app)
    configure_json_logging(app)
    Path(app.config["JOB_STORAGE_DIR"]).mkdir(parents=True, exist_ok=True)

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(api_v1_bp)

    @app.before_request
    def load_request_context():
        mark_request_start()
        incoming = request.headers.get("X-Request-ID", "").strip()
        g.request_id = incoming[:128] if incoming else uuid.uuid4().hex
        g.user = None

        user_id = session.get("user_id")
        if user_id:
            db = app.extensions["db_session"]
            g.user = db.scalar(select(User).where(User.id == user_id))
            if g.user is None:
                session.clear()

    @app.context_processor
    def inject_current_user():
        return {"current_user": g.get("user"), "csrf_token": csrf_token}

    @app.after_request
    def attach_request_id(response):
        observe_response(response)
        if getattr(g, "request_id", None):
            response.headers["X-Request-ID"] = g.request_id
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    @app.errorhandler(413)
    def file_too_large(_error):
        if request.path.startswith("/api/v1/"):
            return api_error(
                "Image is too large. Maximum upload size is 10 MB.",
                code="payload_too_large",
                status=413,
            )
        return {"error": "Image is too large. Maximum upload size is 10 MB."}, 413

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/v1/"):
            return api_error("API endpoint not found.", code="not_found", status=404)
        return _error

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))

