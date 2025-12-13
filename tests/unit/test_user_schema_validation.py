"""
Additional tests for user schema validation and edge cases
"""
import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate


def test_user_schema_password_too_short():
    """Test UserCreate schema with password too short"""
    with pytest.raises(ValidationError, match="at least 8 characters"):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="Pass1!",
            confirm_password="Pass1!"
        )


def test_user_schema_password_no_uppercase():
    """Test UserCreate schema with no uppercase letter"""
    with pytest.raises(ValidationError, match="at least one uppercase letter"):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="password123!",
            confirm_password="password123!"
        )


def test_user_schema_password_no_lowercase():
    """Test UserCreate schema with no lowercase letter"""
    with pytest.raises(ValidationError, match="at least one lowercase letter"):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="PASSWORD123!",
            confirm_password="PASSWORD123!"
        )


def test_user_schema_password_no_digit():
    """Test UserCreate schema with no digit"""
    with pytest.raises(ValidationError, match="at least one digit"):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="Password!",
            confirm_password="Password!"
        )


def test_user_schema_password_no_special():
    """Test UserCreate schema with no special character"""
    with pytest.raises(ValidationError, match="at least one special character"):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="Password123",
            confirm_password="Password123"
        )
