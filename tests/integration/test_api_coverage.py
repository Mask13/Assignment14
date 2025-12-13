"""
API integration tests to cover main.py endpoints and JWT/Redis flows through HTTP.
"""
import pytest
from faker import Faker
from uuid import uuid4

fake = Faker()


@pytest.mark.skip(reason="E2E API tests; run separately to avoid event loop conflicts")
class TestCalculationAPI:
    """Test calculation CRUD endpoints."""
    
    def test_create_calculation_unauthorized(self, fastapi_server):
        """Test creating calculation without authentication."""
        import requests
        response = requests.post(
            f"{fastapi_server}calculations",
            json={"operand1": 5, "operand2": 3, "operation": "add"}
        )
        assert response.status_code == 403
    
    def test_get_calculations_unauthorized(self, fastapi_server):
        """Test retrieving calculations without authentication."""
        import requests
        response = requests.get(f"{fastapi_server}calculations")
        assert response.status_code == 403


@pytest.mark.skip(reason="E2E API tests; run separately to avoid event loop conflicts")
class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_register_duplicate_email(self, fastapi_server):
        """Test registering with duplicate email."""
        import requests
        user_data = {
            "username": fake.user_name(),
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "TestPass123!"
        }
        
        # First registration succeeds
        response1 = requests.post(
            f"{fastapi_server}auth/register",
            json=user_data
        )
        assert response1.status_code == 201
        
        # Second registration with same email fails
        user_data["username"] = fake.user_name()
        response2 = requests.post(
            f"{fastapi_server}auth/register",
            json=user_data
        )
        assert response2.status_code == 400
