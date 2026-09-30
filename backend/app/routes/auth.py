import secrets

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    current_user,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from ..errors import APIError, error_response
from ..extensions import db, jwt, limiter
from ..models import User
from ..validators import validate_login, validate_registration

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

LOGIN_FAILED = "Email or password is incorrect."

_dummy_hash = None


def _dummy_password_hash():
    # When the email is unknown we still check a password against a hash,
    # so the response time does not reveal which emails are registered.
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = generate_password_hash(secrets.token_hex(16))
    return _dummy_hash


def _json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError("Send the form data as JSON.", 400)
    return data


def _logged_in_response(user, status=200):
    response = jsonify({"user": user.to_dict()})
    set_access_cookies(response, create_access_token(identity=str(user.id)))
    return response, status


@bp.post("/register")
@limiter.limit("10 per hour")
def register():
    clean, errors = validate_registration(_json_body())

    if "email" not in errors and User.query.filter_by(email=clean["email"]).first():
        errors["email"] = "An account with this email already exists."
    if errors:
        raise APIError("Please fix the highlighted fields.", 422, errors)

    user = User(name=clean["name"], email=clean["email"])
    user.set_password(clean["password"])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # Two sign-ups with the same email at the same moment.
        db.session.rollback()
        raise APIError(
            "Please fix the highlighted fields.",
            422,
            {"email": "An account with this email already exists."},
        )

    return _logged_in_response(user, 201)


@bp.post("/login")
@limiter.limit("5 per minute; 30 per hour")
def login():
    clean, errors = validate_login(_json_body())
    if errors:
        raise APIError("Please fill in your email and password.", 422, errors)

    user = User.query.filter_by(email=clean["email"]).first()
    if user is None:
        check_password_hash(_dummy_password_hash(), clean["password"])
        raise APIError(LOGIN_FAILED, 401)

    if not user.check_password(clean["password"]):
        raise APIError(LOGIN_FAILED, 401)

    return _logged_in_response(user)


@bp.post("/logout")
def logout():
    # No token required: an expired session must still be able to clear its cookies.
    response = jsonify({"message": "Logged out."})
    unset_jwt_cookies(response)
    return response


@bp.get("/me")
@jwt_required()
def me():
    return {"user": current_user.to_dict()}


# ---- JWT callbacks -------------------------------------------------------


@jwt.user_lookup_loader
def load_user(_header, payload):
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


@jwt.unauthorized_loader
def missing_token(_reason):
    return error_response("Please log in to continue.", 401)


@jwt.invalid_token_loader
def invalid_token(_reason):
    return error_response("Your session is not valid. Please log in again.", 401)


@jwt.expired_token_loader
def expired_token(_header, _payload):
    return error_response("Your session has expired. Please log in again.", 401)


@jwt.user_lookup_error_loader
def user_gone(_header, _payload):
    return error_response("This account no longer exists. Please log in again.", 401)
