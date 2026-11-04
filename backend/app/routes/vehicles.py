from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import current_user, jwt_required

from ..errors import APIError
from ..extensions import db
from ..models import Vehicle
from ..models.vehicle import FIRST_YEAR, MAKE, MODEL_ENGINES, ODOMETER_MAX

bp = Blueprint("vehicles", __name__, url_prefix="/api/vehicles")


def _int(value):
    """Accept 2015 or "2015", reject True, 20.5 and "abc"."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def validate_vehicle(data):
    if not isinstance(data, dict):
        raise APIError("Send the vehicle as JSON.", 400)

    errors = {}
    this_year = date.today().year

    make = data.get("make", MAKE)
    if make != MAKE:
        errors["make"] = f"Only {MAKE} cars are supported."

    model = data.get("model")
    if model not in MODEL_ENGINES:
        errors["model"] = "Choose one of: " + ", ".join(MODEL_ENGINES) + "."

    year = _int(data.get("year"))
    if year is None or not FIRST_YEAR <= year <= this_year:
        errors["year"] = f"Year must be between {FIRST_YEAR} and {this_year}."

    engine_cc = _int(data.get("engine_cc"))
    if "model" not in errors and engine_cc not in MODEL_ENGINES[model]:
        sizes = ", ".join(f"{cc} cc" for cc in MODEL_ENGINES[model])
        errors["engine_cc"] = f"A {model} comes with {sizes}."
    elif "model" in errors and engine_cc is None:
        errors["engine_cc"] = "Choose the engine size."

    odometer = _int(data.get("odometer_km"))
    if odometer is None or not 0 <= odometer <= ODOMETER_MAX:
        errors["odometer_km"] = f"Odometer must be a whole number from 0 to {ODOMETER_MAX:,} km."

    if errors:
        raise APIError("Please fix the highlighted fields.", 422, errors)

    return {
        "make": MAKE,
        "model": model,
        "year": year,
        "engine_cc": engine_cc,
        "odometer_km": odometer,
    }


def get_own_vehicle(vehicle_id):
    """A car that belongs to the logged-in user, or 404 (never 403, so ids don't leak)."""
    vehicle = db.session.execute(
        db.select(Vehicle).filter_by(id=vehicle_id, user_id=current_user.id)
    ).scalar_one_or_none()
    if vehicle is None:
        raise APIError("Vehicle not found.", 404)
    return vehicle


@bp.get("/options")
def options():
    return {
        "make": MAKE,
        "models": [{"name": name, "engines": cc} for name, cc in MODEL_ENGINES.items()],
        "first_year": FIRST_YEAR,
        "last_year": date.today().year,
        "odometer_max": ODOMETER_MAX,
    }


@bp.get("")
@jwt_required()
def list_vehicles():
    vehicles = db.session.execute(
        db.select(Vehicle)
        .filter_by(user_id=current_user.id)
        .order_by(Vehicle.created_at.desc(), Vehicle.id.desc())
    ).scalars()
    return {"vehicles": [v.to_dict() for v in vehicles]}


@bp.post("")
@jwt_required()
def create_vehicle():
    fields = validate_vehicle(request.get_json(silent=True))
    vehicle = Vehicle(user_id=current_user.id, **fields)
    db.session.add(vehicle)
    db.session.commit()
    return {"vehicle": vehicle.to_dict()}, 201


@bp.get("/<int:vehicle_id>")
@jwt_required()
def get_vehicle(vehicle_id):
    return {"vehicle": get_own_vehicle(vehicle_id).to_dict()}


@bp.put("/<int:vehicle_id>")
@jwt_required()
def update_vehicle(vehicle_id):
    vehicle = get_own_vehicle(vehicle_id)
    for key, value in validate_vehicle(request.get_json(silent=True)).items():
        setattr(vehicle, key, value)
    db.session.commit()
    return {"vehicle": vehicle.to_dict()}


@bp.delete("/<int:vehicle_id>")
@jwt_required()
def delete_vehicle(vehicle_id):
    vehicle = get_own_vehicle(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return {"message": "Vehicle deleted."}
