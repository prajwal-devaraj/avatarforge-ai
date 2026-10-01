import os

from flask import Flask, jsonify

from config import DevelopmentConfig, ProductionConfig
from routes.api import api_bp
from routes.pages import pages_bp


def create_app(config_object=None) -> Flask:
    """Application factory for the AvatarForge AI web application."""
    app = Flask(__name__)

    if config_object is None:
        environment = os.environ.get("AVATARFORGE_ENV", "development").lower()
        config_object = ProductionConfig if environment == "production" else DevelopmentConfig

    app.config.from_object(config_object)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(413)
    def file_too_large(_error):
        return jsonify({"error": "Image is too large. Maximum upload size is 10 MB."}), 413

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
