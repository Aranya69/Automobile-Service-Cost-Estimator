from datetime import date

import pytest

from app.extensions import db
from app.models import User, Vehicle

from .conftest import csrf_headers, register

AXIO = {"model": "Axio", "year": 2016, "engine_cc": 1500, "odometer_km": 84000}


def add_car(client, **changes):
    return client.post("/api/vehicles", json={**AXIO, **changes}, headers=csrf_headers(client))


def test_add_and_list_cars(logged_in):
    res = add_car(logged_in)
    assert res.status_code == 201
    car = res.get_json()["vehicle"]
    assert car["make"] == "Toyota"
    assert car["label"] == "Toyota Axio 2016"

    add_car(logged_in, model="Noah", engine_cc=2000, year=2012)
    cars = logged_in.get("/api/vehicles").get_json()["vehicles"]
    assert [c["model"] for c in cars] == ["Noah", "Axio"]  # newest first


def test_numbers_sent_as_strings_are_accepted(logged_in):
    res = add_car(logged_in, year="2018", odometer_km="0", engine_cc="1300")
    assert res.status_code == 201
    assert res.get_json()["vehicle"]["year"] == 2018


@pytest.mark.parametrize(
    "changes, field",
    [
        ({"model": "Prius"}, "model"),
        ({"make": "Honda"}, "make"),
        ({"year": 1994}, "year"),
        ({"year": date.today().year + 1}, "year"),
        ({"year": True}, "year"),
        ({"odometer_km": -1}, "odometer_km"),
        ({"odometer_km": 1_000_000}, "odometer_km"),
        ({"odometer_km": 12.5}, "odometer_km"),
        ({"engine_cc": 2000}, "engine_cc"),  # no 2.0 L Axio
    ],
)
def test_invalid_cars_are_rejected(logged_in, changes, field):
    res = add_car(logged_in, **changes)
    assert res.status_code == 422
    assert field in res.get_json()["fields"]


def test_edit_car(logged_in):
    car_id = add_car(logged_in).get_json()["vehicle"]["id"]
    res = logged_in.put(
        f"/api/vehicles/{car_id}",
        json={**AXIO, "odometer_km": 90500},
        headers=csrf_headers(logged_in),
    )
    assert res.status_code == 200
    assert res.get_json()["vehicle"]["odometer_km"] == 90500
    assert logged_in.get(f"/api/vehicles/{car_id}").get_json()["vehicle"]["odometer_km"] == 90500


def test_delete_car(logged_in):
    car_id = add_car(logged_in).get_json()["vehicle"]["id"]
    assert logged_in.delete(f"/api/vehicles/{car_id}", headers=csrf_headers(logged_in)).status_code == 200
    assert logged_in.get(f"/api/vehicles/{car_id}").status_code == 404


def test_users_cannot_see_each_others_cars(app):
    owner = app.test_client()
    register(owner, email="owner@example.com")
    car_id = add_car(owner).get_json()["vehicle"]["id"]

    other = app.test_client()
    register(other, email="other@example.com")
    headers = csrf_headers(other)
    assert other.get("/api/vehicles").get_json()["vehicles"] == []
    assert other.get(f"/api/vehicles/{car_id}").status_code == 404
    assert other.put(f"/api/vehicles/{car_id}", json=AXIO, headers=headers).status_code == 404
    assert other.delete(f"/api/vehicles/{car_id}", headers=headers).status_code == 404
    assert owner.get(f"/api/vehicles/{car_id}").status_code == 200


def test_login_required(client):
    assert client.get("/api/vehicles").status_code == 401
    assert client.post("/api/vehicles", json=AXIO).status_code == 401


def test_csrf_header_required(logged_in):
    res = logged_in.post("/api/vehicles", json=AXIO)  # no X-CSRF-TOKEN
    assert res.status_code == 401
    assert db.session.execute(db.select(Vehicle)).first() is None


def test_deleting_user_deletes_their_cars(logged_in):
    add_car(logged_in)
    db.session.delete(db.session.execute(db.select(User)).scalar_one())
    db.session.commit()
    assert db.session.execute(db.select(Vehicle)).first() is None


def test_options_list_models(client):
    data = client.get("/api/vehicles/options").get_json()
    assert [m["name"] for m in data["models"]] == ["Axio", "Premio", "Allion", "Corolla", "Noah"]
    assert data["first_year"] == 1995
