"""Fill the database with prices and a demo account for presentations.

    python scripts/seed_demo.py

The demo password is read from DEMO_PASSWORD. If it is not set, a random one is
generated and printed once. Nothing is hardcoded.
"""

import os
import secrets
import string
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app import create_app  # noqa: E402
from app.ai.calculator import calculate_estimate  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Estimate, EstimateItem, User, Vehicle  # noqa: E402
from app.validators import password_error  # noqa: E402
from scripts.import_prices import DATA, run as import_prices  # noqa: E402

DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "demo@asce.test")

CARS = [
    {"model": "Axio", "year": 2016, "engine_cc": 1500, "odometer_km": 84500},
    {"model": "Noah", "year": 2014, "engine_cc": 2000, "odometer_km": 132000},
]

ESTIMATES = [
    # (car index, problem, garage tier, jobs, explanation)
    (0, "brake chaple samner chaka theke awaj ase", "workshop", ["BRAKE_PADS_F"],
     "Front brake pads are probably worn down to the wear indicator."),
    (0, "AC thanda hoy na, batash ase kintu gorom", "local", ["AC_SERVICE"],
     "Low refrigerant is the most common cause. A gas refill and cabin filter usually fix it."),
    (1, "speed breaker e khot khot awaj", "workshop", ["STAB_LINKS", "SHOCKS_F"],
     "Knocking over bumps usually means worn stabilizer links, sometimes front shocks."),
]


def random_password():
    alphabet = string.ascii_letters + string.digits
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(14))
        if password_error(value) is None:
            return value


def seed():
    results = import_prices(DATA / "sample_bikroy_listings.csv", DATA / "sample_garage_prices.csv")
    for source, counts in results.items():
        print(f"Imported {counts['added']} {source} prices")

    if db.session.execute(db.select(User).filter_by(email=DEMO_EMAIL)).scalar_one_or_none():
        print(f"Demo user {DEMO_EMAIL} already exists, leaving it as it is.")
        return

    password = os.environ.get("DEMO_PASSWORD") or random_password()
    problem = password_error(password, DEMO_EMAIL)
    if problem:
        raise SystemExit(f"DEMO_PASSWORD is not valid: {problem}")

    user = User(name="Demo User", email=DEMO_EMAIL)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    cars = [Vehicle(user_id=user.id, **car) for car in CARS]
    db.session.add_all(cars)
    db.session.flush()

    for index, problem_text, tier, jobs, explanation in ESTIMATES:
        car = cars[index]
        result = calculate_estimate(jobs, car.model, tier)
        warnings = [
            f"{job['name_en']} affects safety. Avoid long drives and have a mechanic check it soon."
            for job in result["jobs"]
            if job["safety_critical"]
        ]
        db.session.add(Estimate(
            user_id=user.id,
            vehicle_id=car.id,
            vehicle_label=car.label,
            problem_text=problem_text,
            garage_tier=tier,
            total_min=result["total_min"],
            total_likely=result["total_likely"],
            total_max=result["total_max"],
            confidence=result["confidence"],
            explanation=explanation,
            warnings=warnings,
            method="manual",
            items=[
                EstimateItem(
                    job_code=i["job_code"], kind=i["kind"], description=i["description"],
                    quantity=i["quantity"], price_min=i["price_min"], price_max=i["price_max"],
                    price_count=i["price_count"],
                )
                for i in result["items"]
            ],
        ))

    db.session.commit()
    print(f"Created demo user {DEMO_EMAIL} with {len(cars)} cars and {len(ESTIMATES)} estimates.")
    if not os.environ.get("DEMO_PASSWORD"):
        print(f"Generated password (shown once): {password}")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed()
