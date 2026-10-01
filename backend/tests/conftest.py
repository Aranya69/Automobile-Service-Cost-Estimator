import pytest

from app import create_app
from app.extensions import db

PASSWORD = "garage2024"


def make_app(**overrides):
    app = create_app("testing", overrides or None)
    with app.app_context():
        db.create_all()
    return app


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_headers(client):
    """Header the frontend sends on POST/PUT/DELETE, copied from the CSRF cookie."""
    cookie = client.get_cookie("csrf_access_token")
    return {"X-CSRF-TOKEN": cookie.value} if cookie else {}


def register(client, name="Test User", email="test@example.com", password=PASSWORD):
    return client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )


@pytest.fixture
def logged_in(client):
    res = register(client)
    assert res.status_code == 201
    return client
