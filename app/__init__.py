from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flasgger import Swagger

from config import Config


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Swagger / OpenAPI documentation
    Swagger(
        app,
        template={
            "swagger": "2.0",
            "info": {
                "title": "GDG Confidential Reporting API",
                "description": (
                    "Anonymous and confidential reporting system "
                    "for GDG SRMIST KTR."
                ),
                "version": "1.0.0"
            }
        }
    )

    # Register blueprints
    from app.routes.reports import reports_bp
    from app.routes.moderator import moderator_bp

    app.register_blueprint(
        reports_bp,
        url_prefix="/api"
    )

    app.register_blueprint(
        moderator_bp,
        url_prefix="/api/moderator"
    )

    # Health check
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app