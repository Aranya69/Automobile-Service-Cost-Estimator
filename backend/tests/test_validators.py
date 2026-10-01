import pytest

from app.validators import (
    name_error,
    normalize_email,
    password_error,
    validate_login,
    validate_registration,
)


def good(**changes):
    data = {
        "name": "Tanima Akter",
        "email": "tanima@example.com",
        "password": "garage2024",
        "confirm_password": "garage2024",
    }
    data.update(changes)
    return data


def test_valid_registration_has_no_errors():
    clean, errors = validate_registration(good())
    assert errors == {}
    assert clean == {"name": "Tanima Akter", "email": "tanima@example.com", "password": "garage2024"}


def test_name_spaces_are_collapsed():
    clean, _ = validate_registration(good(name="  Tanima    Akter "))
    assert clean["name"] == "Tanima Akter"


@pytest.mark.parametrize("name", ["", "A", "x" * 61, "12345", "Ta\x00nima"])
def test_bad_names(name):
    assert name_error(" ".join(name.split())) is not None


def test_bangla_name_is_allowed():
    assert name_error("তানিমা আক্তার") is None


def test_email_is_lowercased():
    email, err = normalize_email("  Tanima@Example.COM ")
    assert err is None
    assert email == "tanima@example.com"


@pytest.mark.parametrize("email", ["", "tanima", "tanima@", "@example.com", "a b@example.com"])
def test_bad_emails(email):
    _, err = normalize_email(email)
    assert err is not None


@pytest.mark.parametrize(
    "password, fragment",
    [
        ("", "required"),
        ("abc123", "at least 8"),
        ("abcdefgh", "letter and one number"),
        ("12345678", "letter and one number"),
        ("a1" * 65, "at most 128"),
    ],
)
def test_bad_passwords(password, fragment):
    assert fragment in password_error(password)


def test_password_cannot_equal_email():
    assert password_error("tanima1@example.com", "Tanima1@example.com") is not None


def test_confirm_password_must_match():
    _, errors = validate_registration(good(confirm_password="garage2025"))
    assert errors == {"confirm_password": "Passwords do not match."}


def test_non_string_values_are_treated_as_missing():
    _, errors = validate_registration({"name": 42, "email": ["x"], "password": None})
    assert set(errors) == {"name", "email", "password", "confirm_password"}


def test_login_requires_both_fields():
    _, errors = validate_login({})
    assert set(errors) == {"email", "password"}
