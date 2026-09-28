import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

MIN_SECRET_LENGTH = 32


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def required_secret(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy backend/.env.example to backend/.env and fill it in."
        )
    if len(value) < MIN_SECRET_LENGTH:
        raise RuntimeError(f"{name} must be at least {MIN_SECRET_LENGTH} characters long.")
    return value


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # JWT lives in an HTTP-only cookie. Flask-JWT-Extended also sets a
    # readable csrf_access_token cookie that the frontend sends back as a header.
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_COOKIE_SECURE = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    JWT_COOKIE_SECURE = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


CONFIGS = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def load_config(app, name):
    if name not in CONFIGS:
        raise RuntimeError(f"Unknown APP_ENV '{name}'. Use one of: {', '.join(CONFIGS)}")

    config = CONFIGS[name]
    app.config.from_object(config)

    if config is TestingConfig:
        # Throwaway keys for each test run, so tests need no .env file.
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        app.config["JWT_SECRET_KEY"] = secrets.token_hex(32)
        return

    app.config["SECRET_KEY"] = required_secret("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = required_secret("JWT_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "asce.db")
    )
    app.config["JWT_COOKIE_SECURE"] = env_bool("COOKIE_SECURE", config.JWT_COOKIE_SECURE)
