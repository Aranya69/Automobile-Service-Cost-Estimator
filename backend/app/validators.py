import re
import unicodedata

from email_validator import EmailNotValidError, validate_email

NAME_MIN = 2
NAME_MAX = 60
EMAIL_MAX = 254
PASSWORD_MIN = 8
PASSWORD_MAX = 128

HAS_LETTER = re.compile(r"[A-Za-z]")
HAS_DIGIT = re.compile(r"\d")


def _text(data, key):
    value = data.get(key) if isinstance(data, dict) else None
    return value if isinstance(value, str) else ""


def clean_name(raw):
    # Collapse runs of spaces so "  Rahim   Uddin " becomes "Rahim Uddin".
    return " ".join(raw.split())


def name_error(name):
    if not name:
        return "Name is required."
    if len(name) < NAME_MIN or len(name) > NAME_MAX:
        return f"Name must be {NAME_MIN} to {NAME_MAX} characters."
    if any(unicodedata.category(ch).startswith("C") for ch in name):
        return "Name contains characters that are not allowed."
    if not any(ch.isalpha() for ch in name):
        return "Name must contain letters."
    return None


def normalize_email(raw):
    """Return (email, error). The email is lower-cased so lookups are case-insensitive."""
    raw = raw.strip()
    if not raw:
        return None, "Email is required."
    if len(raw) > EMAIL_MAX:
        return None, "Email is too long."
    try:
        result = validate_email(raw, check_deliverability=False)
    except EmailNotValidError:
        return None, "Enter a valid email address."
    return result.normalized.lower(), None


def password_error(password, email=None):
    if not password:
        return "Password is required."
    if len(password) < PASSWORD_MIN:
        return f"Password must be at least {PASSWORD_MIN} characters."
    if len(password) > PASSWORD_MAX:
        return f"Password must be at most {PASSWORD_MAX} characters."
    if not HAS_LETTER.search(password) or not HAS_DIGIT.search(password):
        return "Password must contain at least one letter and one number."
    if email and password.lower() == email.lower():
        return "Password must not be the same as your email."
    return None


def validate_registration(data):
    """Return (clean_data, errors). errors maps field name to message."""
    errors = {}

    name = clean_name(_text(data, "name"))
    err = name_error(name)
    if err:
        errors["name"] = err

    email, err = normalize_email(_text(data, "email"))
    if err:
        errors["email"] = err

    password = _text(data, "password")
    err = password_error(password, email)
    if err:
        errors["password"] = err

    confirm = _text(data, "confirm_password")
    if not confirm:
        errors["confirm_password"] = "Please confirm your password."
    elif confirm != password:
        errors["confirm_password"] = "Passwords do not match."

    return {"name": name, "email": email, "password": password}, errors


def validate_login(data):
    errors = {}
    email = _text(data, "email").strip().lower()
    password = _text(data, "password")
    if not email:
        errors["email"] = "Email is required."
    if not password:
        errors["password"] = "Password is required."
    return {"email": email, "password": password}, errors
