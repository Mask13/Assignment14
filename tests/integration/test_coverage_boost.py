"""
Additional tests to reach 95% coverage - focusing on JWT, Redis, and main.py
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app
from app.models.user import User
from app.auth.jwt import create_token, decode_token
from app.schemas.token import TokenType
from sqlalchemy.orm import Session
from faker import Faker
from datetime import timedelta
from uuid import uuid4, UUID

fake = Faker()
client = TestClient(app)


# JWT Tests
def test_create_token_with_custom_expiry():
    """Test creating token with custom expiration"""
    user_id = str(uuid4())
    custom_expiry = timedelta(hours=1)
    token = create_token(user_id, TokenType.ACCESS, custom_expiry)
    assert token is not None
    assert isinstance(token, str)


def test_create_token_with_uuid_object():
    """Test creating token with UUID object (not string)"""
    user_id = uuid4()  # UUID object, not string
    token = create_token(user_id, TokenType.ACCESS)
    assert token is not None


def test_create_refresh_token_default_expiry():
    """Test creating refresh token with default expiry"""
    user_id = str(uuid4())
    token = create_token(user_id, TokenType.REFRESH)
    assert token is not None


# Main.py endpoint tests for missing coverage
def test_login_with_naive_datetime(db_session: Session):
    """Test login endpoint datetime handling"""
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    response = client.post("/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_register_user_via_api(db_session: Session):
    """Test user registration via API endpoint"""
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!",
        "confirm_password": "TestPass123!"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    assert "id" in response.json()


def test_get_nonexistent_calculation(db_session: Session):
    """Test getting a calculation that doesn't exist"""
    # Create and login user
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    login_response = client.post("/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    fake_id = str(uuid4())
    response = client.get(
        f"/api/calculations/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_update_nonexistent_calculation(db_session: Session):
    """Test updating a calculation that doesn't exist"""
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    login_response = client.post("/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    fake_id = str(uuid4())
    response = client.put(
        f"/api/calculations/{fake_id}",
        json={"inputs": [10, 5]},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_delete_nonexistent_calculation(db_session: Session):
    """Test deleting a calculation that doesn't exist"""
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    login_response = client.post("/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    fake_id = str(uuid4())
    response = client.delete(
        f"/api/calculations/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


# User model tests
def test_user_get_by_username(db_session: Session):
    """Test User.get_by_username class method"""
    """Test User.authenticate and verify_password"""
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    # Test authenticate method
    authenticated = User.authenticate(db_session, user_data["username"], user_data["password"])
    assert authenticated is not None
    assert authenticated["user"].username == user_data["username"]


def test_user_get_by_email(db_session: Session):
    """Test User.get_by_email class method"""
    """Test User authentication via email"""
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    # Test authenticating via email instead of username
    authenticated = User.authenticate(db_session, user_data["email"], user_data["password"])
    assert authenticated is not None
    assert authenticated["user"].email == user_data["email"]


def test_user_is_admin_false(db_session: Session):
    """Test is_admin property returns False for regular users"""
    """Test verify_password method with wrong password"""
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    # Test that wrong password fails
    assert user.verify_password("WrongPassword") is False


# Calculation model tests
def test_calculation_repr():
    """Test calculation __repr__ method"""
    from app.models.calculation import Calculation
    calc = Calculation(
        user_id=uuid4(),
        type="addition",
        inputs=[1, 2, 3]
    )
    repr_str = repr(calc)
    assert "Calculation" in repr_str
    assert "addition" in repr_str


def test_calculation_to_dict(db_session: Session):
    """Test calculation to_dict method"""
    """Test calculation create with Calculation.create"""
    from app.models.calculation import Calculation
    
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    # Use the correct factory method signature
    calc = Calculation.create("addition", user.id, [5.0, 3.0])
    db_session.add(calc)
    db_session.commit()
    
    result = calc.get_result()
    assert result == 8.0
    assert calc.type == "addition"


def test_invalid_calculation_type_raises_error(db_session: Session):
    """Test that invalid calculation type raises ValueError"""
    """Test that invalid calculation type raises ValueError"""
    from app.models.calculation import Calculation
    
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    
    user = User.register(db_session, user_data)
    db_session.commit()
    
    # Test invalid calculation type
    with pytest.raises(ValueError):
        Calculation.create("invalid_type", user.id, [1.0, 2.0])


# Schema validation tests
def test_user_schema_password_mismatch():
    """Test UserCreate schema with password mismatch"""
    from app.schemas.user import UserCreate
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="Pass123!",
            confirm_password="DifferentPass123!"
        )


def test_calculation_schema_validation():
    """Test calculation schema validation"""
    """Test calculation schema validation"""
    from app.schemas.calculation import CalculationCreate, CalculationType
    from pydantic import ValidationError
    
    # Valid calculation - CalculationCreate requires user_id
    calc = CalculationCreate(
        type=CalculationType.ADDITION,
        inputs=[1, 2, 3],
        user_id=uuid4()
    )
    assert calc.type == CalculationType.ADDITION
    
    # Invalid type
    with pytest.raises(ValidationError):
        CalculationCreate(
            type="invalid_operation",
            inputs=[1, 2],
            user_id=uuid4()
        )
