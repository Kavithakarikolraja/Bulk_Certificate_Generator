import pytest
from app.services.validator import validate_recipient_data

def test_validate_valid_recipient():
    is_valid, err = validate_recipient_data(name="John Doe", email="john@example.com")
    assert is_valid is True
    assert err is None

def test_validate_missing_name():
    is_valid, err = validate_recipient_data(name="", email="john@example.com")
    assert is_valid is False
    assert "required" in err.lower()

def test_validate_short_name():
    is_valid, err = validate_recipient_data(name="A", email="a@example.com")
    assert is_valid is False
    assert "at least 2 characters" in err.lower()

def test_validate_invalid_email():
    is_valid, err = validate_recipient_data(name="John Doe", email="not-an-email")
    assert is_valid is False
    assert "invalid email format" in err.lower()

def test_validate_optional_email_none():
    is_valid, err = validate_recipient_data(name="Jane Doe", email=None)
    assert is_valid is True
    assert err is None
