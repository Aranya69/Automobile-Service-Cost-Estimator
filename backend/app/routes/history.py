from flask import Blueprint, request
from flask_jwt_extended import current_user, jwt_required

from ..errors import APIError
from ..extensions import db
from ..models import Estimate

bp = Blueprint("history", __name__, url_prefix="/api/estimates")

PER_PAGE_DEFAULT = 20
PER_PAGE_MAX = 50


def _positive_int(name, default, maximum=None):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    if not raw.isdigit() or int(raw) < 1:
        raise APIError(f"'{name}' must be a positive whole number.", 400)
    value = int(raw)
    return min(value, maximum) if maximum else value


def get_own_estimate(estimate_id):
    estimate = db.session.execute(
        db.select(Estimate).filter_by(id=estimate_id, user_id=current_user.id)
    ).scalar_one_or_none()
    if estimate is None:
        raise APIError("Estimate not found.", 404)
    return estimate


@bp.get("")
@jwt_required()
def list_estimates():
    page = _positive_int("page", 1)
    per_page = _positive_int("per_page", PER_PAGE_DEFAULT, PER_PAGE_MAX)
    vehicle_id = request.args.get("vehicle_id")

    query = db.select(Estimate).filter_by(user_id=current_user.id)
    if vehicle_id:
        if not vehicle_id.isdigit():
            raise APIError("'vehicle_id' must be a number.", 400)
        query = query.filter_by(vehicle_id=int(vehicle_id))

    total = db.session.execute(
        db.select(db.func.count()).select_from(query.subquery())
    ).scalar_one()
    estimates = db.session.execute(
        query.order_by(Estimate.created_at.desc(), Estimate.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).scalars()

    return {
        "estimates": [e.to_dict() for e in estimates],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@bp.get("/<int:estimate_id>")
@jwt_required()
def get_estimate(estimate_id):
    return {"estimate": get_own_estimate(estimate_id).to_dict(with_items=True)}


@bp.delete("/<int:estimate_id>")
@jwt_required()
def delete_estimate(estimate_id):
    estimate = get_own_estimate(estimate_id)
    db.session.delete(estimate)
    db.session.commit()
    return {"message": "Estimate deleted."}
