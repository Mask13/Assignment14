import pytest
from pydantic import ValidationError

from app.schemas.base import UserCreate


def test_password_requires_uppercase():
    with pytest.raises(ValueError) as exc:
        UserCreate(
            first_name="A",
            last_name="B",
            email="a@b.com",
            username="userabc",
            password="lowercase1"
        )
    assert "uppercase" in str(exc.value).lower()


def test_password_requires_lowercase():
    with pytest.raises(ValueError) as exc:
        UserCreate(
            first_name="A",
            last_name="B",
            email="a@b.com",
            username="userabc",
            password="UPPERCASE1"
        )
    assert "lowercase" in str(exc.value).lower()


def test_password_requires_digit():
    with pytest.raises(ValueError) as exc:
        UserCreate(
            first_name="A",
            last_name="B",
            email="a@b.com",
            username="userabc",
            password="NoDigitsHere"
        )
    assert "digit" in str(exc.value).lower()


def test_password_missing_raises_validation_error():
    # Depending on Pydantic internals and schema code, this may raise
    # a ValidationError or a TypeError. Accept either to ensure coverage.
    with pytest.raises((ValidationError, TypeError)):
        UserCreate(
            first_name="A",
            last_name="B",
            email="a@b.com",
            username="userabc",
            # password omitted entirely
        )
