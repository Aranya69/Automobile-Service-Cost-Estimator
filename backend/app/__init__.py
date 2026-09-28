import os

from flask import Flask

from .config import load_config
from .errors import register_error_handlers
from .extensions import db, jwt, migrate


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    load_config(app, config_name or os.environ.get("APP_ENV", "development"))

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    register_error_handlers(app)

    from . import models  # noqa: F401  (registers tables with SQLAlchemy)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
