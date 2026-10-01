import os

from flask import Flask

from .config import load_config
from .errors import register_error_handlers
from .extensions import db, jwt, limiter, migrate


def create_app(config_name=None, overrides=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    load_config(app, config_name or os.environ.get("APP_ENV", "development"))
    if overrides:
        app.config.update(overrides)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    register_error_handlers(app)

    from . import models  # noqa: F401  (registers tables with SQLAlchemy)
    from .routes.auth import bp as auth_bp

    app.register_blueprint(auth_bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
