from app.extensions import db
from app.models import User

from .conftest import PASSWORD, make_app, register


def test_register_creates_user_and_logs_in(client):
    res = register(client, email="Meher@Example.com")
    assert res.status_code == 201
    body = res.get_json()
    assert body["user"]["email"] == "meher@example.com"
    assert "password" not in str(body)

    assert client.get_cookie("access_token_cookie") is not None
    assert client.get_cookie("csrf_access_token") is not None
    assert client.get("/api/auth/me").status_code == 200


def test_password_is_hashed(client, app):
    register(client)
    user = db.session.execute(db.select(User)).scalar_one()
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("scrypt:")
    assert user.check_password(PASSWORD)
    assert not user.check_password("wrong-password1")


def test_auth_cookie_is_http_only(client):
    res = register(client)
    cookies = res.headers.getlist("Set-Cookie")
    access = next(c for c in cookies if c.startswith("access_token_cookie="))
    csrf = next(c for c in cookies if c.startswith("csrf_access_token="))
    assert "HttpOnly" in access
    assert "SameSite=Lax" in access
    assert "HttpOnly" not in csrf  # the frontend has to read this one


def test_register_rejects_duplicate_email(client):
    register(client)
    client.post("/api/auth/logout")
    res = register(client, email="TEST@example.com")
    assert res.status_code == 422
    assert "already exists" in res.get_json()["fields"]["email"]


def test_register_returns_field_errors(client):
    res = client.post("/api/auth/register", json={"name": "A", "email": "bad"})
    assert res.status_code == 422
    fields = res.get_json()["fields"]
    assert set(fields) == {"name", "email", "password", "confirm_password"}
    assert client.get_cookie("access_token_cookie") is None


def test_register_requires_json(client):
    res = client.post("/api/auth/register", data="name=x", content_type="text/plain")
    assert res.status_code == 400


def test_login_with_correct_password(client):
    register(client)
    client.post("/api/auth/logout")
    res = client.post("/api/auth/login", json={"email": "Test@Example.com", "password": PASSWORD})
    assert res.status_code == 200
    assert res.get_json()["user"]["email"] == "test@example.com"
    assert client.get("/api/auth/me").status_code == 200


def test_login_wrong_password_and_unknown_email_look_the_same(client):
    register(client)
    client.post("/api/auth/logout")
    wrong = client.post("/api/auth/login", json={"email": "test@example.com", "password": "nope12345"})
    unknown = client.post("/api/auth/login", json={"email": "who@example.com", "password": "nope12345"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()


def test_me_requires_login(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert res.get_json()["message"] == "Please log in to continue."


def test_tampered_token_is_rejected(client):
    register(client)
    token = client.get_cookie("access_token_cookie").value
    client.set_cookie("access_token_cookie", token[:-4] + "abcd")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_session(logged_in):
    res = logged_in.post("/api/auth/logout")
    assert res.status_code == 200
    assert logged_in.get_cookie("access_token_cookie") is None
    assert logged_in.get("/api/auth/me").status_code == 401


def test_deleted_user_session_is_rejected(logged_in, app):
    db.session.execute(db.delete(User))
    db.session.commit()
    assert logged_in.get("/api/auth/me").status_code == 401


def test_login_is_rate_limited():
    app = make_app(RATELIMIT_ENABLED=True)
    client = app.test_client()
    codes = [
        client.post(
            "/api/auth/login", json={"email": "x@example.com", "password": "nope12345"}
        ).status_code
        for _ in range(6)
    ]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429
