import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.database import get_db
from app.models.user import User
from app.models.calculation import Calculation

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass 
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_register_user(client):
    response = client.post(
        "/users/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "Password123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login_user(client):
    # Register first
    client.post(
        "/users/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "Password123",
            "first_name": "Login",
            "last_name": "User"
        }
    )
    
    # Login
    response = client.post(
        "/users/login",
        data={
            "username": "loginuser",
            "password": "Password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_calculation(client):
    # Register and login
    client.post(
        "/users/register",
        json={
            "email": "calc@example.com",
            "username": "calcuser",
            "password": "Password123",
            "first_name": "Calc",
            "last_name": "User"
        }
    )
    login_res = client.post(
        "/users/login",
        data={
            "username": "calcuser",
            "password": "Password123"
        }
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create calculation
    response = client.post(
        "/calculations",
        json={
            "type": "addition",
            "inputs": [10, 5]
        },
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["result"] == 15
    assert data["type"] == "addition"

def test_read_calculations(client):
    # Register and login
    client.post(
        "/users/register",
        json={
            "email": "read@example.com",
            "username": "readuser",
            "password": "Password123",
            "first_name": "Read",
            "last_name": "User"
        }
    )
    login_res = client.post(
        "/users/login",
        data={
            "username": "readuser",
            "password": "Password123"
        }
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create calculation
    client.post(
        "/calculations",
        json={"type": "subtraction", "inputs": [10, 5]},
        headers=headers
    )
    
    # Read calculations
    response = client.get("/calculations", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # We can't guarantee order or exact content if other tests run, but we can check if our calc is there
    # Or just check structure

def test_update_calculation(client):
    # Register and login
    client.post(
        "/users/register",
        json={
            "email": "update@example.com",
            "username": "updateuser",
            "password": "Password123",
            "first_name": "Update",
            "last_name": "User"
        }
    )
    login_res = client.post(
        "/users/login",
        data={
            "username": "updateuser",
            "password": "Password123"
        }
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create calculation
    create_res = client.post(
        "/calculations",
        json={"type": "multiplication", "inputs": [2, 3]},
        headers=headers
    )
    calc_id = create_res.json()["id"]
    
    # Update calculation
    response = client.put(
        f"/calculations/{calc_id}",
        json={"inputs": [4, 5]},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == 20
    assert data["inputs"] == [4.0, 5.0]

def test_delete_calculation(client):
    # Register and login
    client.post(
        "/users/register",
        json={
            "email": "delete@example.com",
            "username": "deleteuser",
            "password": "Password123",
            "first_name": "Delete",
            "last_name": "User"
        }
    )
    login_res = client.post(
        "/users/login",
        data={
            "username": "deleteuser",
            "password": "Password123"
        }
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create calculation
    create_res = client.post(
        "/calculations",
        json={"type": "division", "inputs": [10, 2]},
        headers=headers
    )
    calc_id = create_res.json()["id"]
    
    # Delete calculation
    response = client.delete(f"/calculations/{calc_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify deletion
    get_res = client.get(f"/calculations/{calc_id}", headers=headers)
    assert get_res.status_code == 404

def test_invalid_calculation(client):
    # Register and login
    client.post(
        "/users/register",
        json={
            "email": "invalid@example.com",
            "username": "invaliduser",
            "password": "Password123",
            "first_name": "Invalid",
            "last_name": "User"
        }
    )
    login_res = client.post(
        "/users/login",
        data={
            "username": "invaliduser",
            "password": "Password123"
        }
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Division by zero
    response = client.post(
        "/calculations",
        json={"type": "division", "inputs": [10, 0]},
        headers=headers
    )
    # The schema validator might catch this if configured, or the model.
    # In CalculationBase schema:
    # @model_validator(mode="after")
    # def validate_division_by_zero(self) -> "CalculationBase":
    # So it should be 422 Unprocessable Entity (Pydantic validation error)
    # BUT main.py has a custom exception handler for RequestValidationError that returns 400
    assert response.status_code == 400
    
    # Invalid type
    response = client.post(
        "/calculations",
        json={"type": "invalid", "inputs": [10, 5]},
        headers=headers
    )
    assert response.status_code == 400