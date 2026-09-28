import pytest

from app import create_app


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_unknown_route_returns_json(client):
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    assert "message" in res.get_json()


def test_missing_secret_stops_startup(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 40)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("development")


def test_short_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "short")
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 40)
    with pytest.raises(RuntimeError, match="at least"):
        create_app("development")
