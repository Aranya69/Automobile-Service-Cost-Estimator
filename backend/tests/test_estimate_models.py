from app.extensions import db
from app.models import Estimate, EstimateItem, User, Vehicle


def make_estimate(user, vehicle):
    estimate = Estimate(
        user_id=user.id,
        vehicle_id=vehicle.id,
        vehicle_label=vehicle.label,
        problem_text="brake e awaj kore",
        garage_tier="workshop",
        total_min=3200,
        total_likely=4100,
        total_max=5300,
        confidence="high",
        explanation="Front pads are worn.",
        warnings=["Brakes are safety critical."],
        items=[
            EstimateItem(job_code="BRAKE_PADS_F", kind="part", description="Front brake pads (set)",
                         quantity=1, price_min=2500, price_max=4100, price_count=6),
            EstimateItem(job_code="BRAKE_PADS_F", kind="labour", description="Labour 1.0 h",
                         quantity=1, price_min=700, price_max=1200, price_count=1),
        ],
    )
    db.session.add(estimate)
    db.session.commit()
    return estimate


def setup_user_and_car():
    user = User(name="Jannat", email="jannat@example.com")
    user.set_password("garage2024")
    db.session.add(user)
    db.session.flush()
    car = Vehicle(user_id=user.id, model="Axio", year=2016, engine_cc=1500, odometer_km=80000)
    db.session.add(car)
    db.session.commit()
    return user, car


def test_estimate_with_items(app):
    user, car = setup_user_and_car()
    estimate = make_estimate(user, car)
    data = estimate.to_dict(with_items=True)
    assert data["vehicle_label"] == "Toyota Axio 2016"
    assert [i["kind"] for i in data["items"]] == ["part", "labour"]
    assert data["warnings"] == ["Brakes are safety critical."]
    assert "items" not in estimate.to_dict()


def test_deleting_car_keeps_estimate(app):
    user, car = setup_user_and_car()
    estimate_id = make_estimate(user, car).id
    db.session.delete(car)
    db.session.commit()
    db.session.expire_all()
    kept = db.session.get(Estimate, estimate_id)
    assert kept is not None
    assert kept.vehicle_id is None
    assert kept.vehicle_label == "Toyota Axio 2016"


def test_deleting_estimate_deletes_items(app):
    user, car = setup_user_and_car()
    estimate = make_estimate(user, car)
    db.session.delete(estimate)
    db.session.commit()
    assert db.session.execute(db.select(EstimateItem)).first() is None
