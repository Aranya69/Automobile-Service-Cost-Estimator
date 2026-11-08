from app.extensions import db
from app.models import Estimate, User, Vehicle
from scripts import seed_demo


def test_seed_creates_demo_account(app, monkeypatch, capsys):
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    seed_demo.seed()
    out = capsys.readouterr().out
    assert "Generated password" in out

    user = db.session.execute(db.select(User).filter_by(email=seed_demo.DEMO_EMAIL)).scalar_one()
    password = out.split("Generated password (shown once): ")[1].strip()
    assert user.check_password(password)
    assert db.session.execute(db.select(db.func.count()).select_from(Vehicle)).scalar() == 2
    assert db.session.execute(db.select(db.func.count()).select_from(Estimate)).scalar() == 3


def test_seed_uses_password_from_env(app, monkeypatch, capsys):
    monkeypatch.setenv("DEMO_PASSWORD", "presentation2026")
    seed_demo.seed()
    assert "Generated password" not in capsys.readouterr().out
    user = db.session.execute(db.select(User).filter_by(email=seed_demo.DEMO_EMAIL)).scalar_one()
    assert user.check_password("presentation2026")


def test_seed_twice_does_not_duplicate(app, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "presentation2026")
    seed_demo.seed()
    seed_demo.seed()
    assert db.session.execute(db.select(db.func.count()).select_from(User)).scalar() == 1
