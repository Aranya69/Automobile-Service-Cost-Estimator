from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models import Estimate, EstimateItem, User, Vehicle

from .conftest import csrf_headers, register


def current_user_id():
    return db.session.execute(db.select(User.id).order_by(User.id.desc())).scalars().first()


def add_car(client, model="Axio", engine_cc=1500):
    res = client.post(
        "/api/vehicles",
        json={"model": model, "year": 2015, "engine_cc": engine_cc, "odometer_km": 100000},
        headers=csrf_headers(client),
    )
    return res.get_json()["vehicle"]["id"]


def add_estimate(user_id, vehicle_id, problem="brake e awaj", minutes_ago=0):
    vehicle = db.session.get(Vehicle, vehicle_id)
    estimate = Estimate(
        user_id=user_id,
        vehicle_id=vehicle_id,
        vehicle_label=vehicle.label,
        problem_text=problem,
        garage_tier="workshop",
        total_min=3000,
        total_likely=4000,
        total_max=5000,
        confidence="medium",
        explanation="Front pads.",
        warnings=["Check brakes soon."],
        created_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
        items=[EstimateItem(job_code="BRAKE_PADS_F", kind="part", description="Front brake pads (set)",
                            quantity=1, price_min=2300, price_max=3800, price_count=4)],
    )
    db.session.add(estimate)
    db.session.commit()
    return estimate.id


@pytest.fixture
def user_with_estimates(logged_in):
    car = add_car(logged_in)
    uid = current_user_id()
    old = add_estimate(uid, car, "AC thanda hoy na", minutes_ago=60)
    new = add_estimate(uid, car, "brake e awaj kore", minutes_ago=1)
    return logged_in, car, old, new


def test_list_newest_first(user_with_estimates):
    client, _, old, new = user_with_estimates
    data = client.get("/api/estimates").get_json()
    assert [e["id"] for e in data["estimates"]] == [new, old]
    assert data["total"] == 2
    assert "items" not in data["estimates"][0]  # list stays light


def test_detail_includes_items(user_with_estimates):
    client, _, _, new = user_with_estimates
    data = client.get(f"/api/estimates/{new}").get_json()["estimate"]
    assert data["items"][0]["description"] == "Front brake pads (set)"
    assert data["warnings"] == ["Check brakes soon."]
    assert data["vehicle_label"] == "Toyota Axio 2015"


def test_delete(user_with_estimates):
    client, _, old, new = user_with_estimates
    res = client.delete(f"/api/estimates/{old}", headers=csrf_headers(client))
    assert res.status_code == 200
    assert client.get(f"/api/estimates/{old}").status_code == 404
    assert [e["id"] for e in client.get("/api/estimates").get_json()["estimates"]] == [new]
    assert db.session.execute(db.select(EstimateItem).filter_by(estimate_id=old)).first() is None


def test_delete_needs_csrf(user_with_estimates):
    client, _, old, _ = user_with_estimates
    assert client.delete(f"/api/estimates/{old}").status_code == 401
    assert client.get(f"/api/estimates/{old}").status_code == 200


def test_filter_by_vehicle(user_with_estimates):
    client, car, _, _ = user_with_estimates
    other_car = add_car(client, model="Noah", engine_cc=2000)
    add_estimate(current_user_id(), other_car)
    assert client.get(f"/api/estimates?vehicle_id={other_car}").get_json()["total"] == 1
    assert client.get(f"/api/estimates?vehicle_id={car}").get_json()["total"] == 2


def test_pagination(user_with_estimates):
    client, _, old, new = user_with_estimates
    page1 = client.get("/api/estimates?per_page=1").get_json()
    page2 = client.get("/api/estimates?per_page=1&page=2").get_json()
    assert [e["id"] for e in page1["estimates"]] == [new]
    assert [e["id"] for e in page2["estimates"]] == [old]
    assert client.get("/api/estimates?page=0").status_code == 400
    assert client.get("/api/estimates?per_page=500").get_json()["per_page"] == 50


def test_history_survives_car_deletion(user_with_estimates):
    client, car, _, new = user_with_estimates
    client.delete(f"/api/vehicles/{car}", headers=csrf_headers(client))
    data = client.get(f"/api/estimates/{new}").get_json()["estimate"]
    assert data["vehicle_id"] is None
    assert data["vehicle_label"] == "Toyota Axio 2015"


def test_other_users_cannot_see_or_delete(app, user_with_estimates):
    _, _, old, _ = user_with_estimates
    stranger = app.test_client()
    register(stranger, email="stranger@example.com")
    assert stranger.get("/api/estimates").get_json()["total"] == 0
    assert stranger.get(f"/api/estimates/{old}").status_code == 404
    assert stranger.delete(f"/api/estimates/{old}", headers=csrf_headers(stranger)).status_code == 404


def test_login_required(client):
    assert client.get("/api/estimates").status_code == 401
    assert client.get("/api/estimates/1").status_code == 401


def test_sort_by_cost(user_with_estimates):
    client, car, old, new = user_with_estimates
    cheap = db.session.get(Estimate, new)
    cheap.total_likely = 1000
    db.session.commit()
    ids = [e["id"] for e in client.get("/api/estimates?sort=cost").get_json()["estimates"]]
    assert ids == [old, new]
    assert client.get("/api/estimates?sort=random").status_code == 400


def test_filter_by_days(user_with_estimates):
    client, car, old, new = user_with_estimates
    ancient = db.session.get(Estimate, old)
    ancient.created_at = datetime.now(timezone.utc) - timedelta(days=200)
    db.session.commit()
    assert [e["id"] for e in client.get("/api/estimates?days=30").get_json()["estimates"]] == [new]
    assert client.get("/api/estimates?days=365").get_json()["total"] == 2
    assert client.get("/api/estimates?days=abc").status_code == 400
