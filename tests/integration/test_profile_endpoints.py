"""
Integration tests for user profile endpoints
Tests profile retrieval, updates, and password changes with database interactions
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db
from app.models.user import User


@pytest.fixture
def client(db_session):
    """Create a test client with database session override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass 
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_user(client):
    """Create and authenticate a test user with unique credentials"""
    # Generate unique credentials for each test
    unique_id = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_id}"
    email = f"testuser_{unique_id}@example.com"
    
    # Register user
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "Password123!",
            "confirm_password": "Password123!",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert register_response.status_code == 201
    
    # Login to get token
    login_response = client.post(
        "/auth/token",
        data={
            "username": username,
            "password": "Password123!"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    return {
        "token": token,
        "username": username,
        "email": email,
        "headers": {"Authorization": f"Bearer {token}"}
    }


# ======================================================================================
# Get Profile Tests
# ======================================================================================

def test_get_current_user_profile_success(client, authenticated_user):
    """Test successfully retrieving current user's profile"""
    response = client.get(
        "/users/me",
        headers=authenticated_user["headers"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == authenticated_user["username"]
    assert data["email"] == authenticated_user["email"]
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["is_active"] is True


def test_get_current_user_profile_no_auth(client):
    """Test getting profile without authentication fails"""
    response = client.get("/users/me")
    assert response.status_code == 401


def test_get_current_user_profile_invalid_token(client):
    """Test getting profile with invalid token fails"""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token_12345"}
    )
    assert response.status_code == 401


# ======================================================================================
# Update Profile Tests
# ======================================================================================

def test_update_profile_all_fields(client, authenticated_user, db_session):
    """Test updating all profile fields successfully"""
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "email": "updated@example.com",
            "username": "updateduser"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "UpdatedFirst"
    assert data["last_name"] == "UpdatedLast"
    assert data["email"] == "updated@example.com"
    assert data["username"] == "updateduser"
    
    # Verify in database
    user = db_session.query(User).filter(User.username == "updateduser").first()
    assert user is not None
    assert user.first_name == "UpdatedFirst"
    assert user.email == "updated@example.com"


def test_update_profile_partial_fields(client, authenticated_user, db_session):
    """Test updating only some profile fields"""
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "first_name": "NewFirst",
            "last_name": "NewLast"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "NewFirst"
    assert data["last_name"] == "NewLast"
    # Email and username should remain unchanged
    assert data["email"] == authenticated_user["email"]
    assert data["username"] == authenticated_user["username"]


def test_update_profile_email_only(client, authenticated_user):
    """Test updating only email"""
    new_email = f"newemail_{str(uuid.uuid4())[:8]}@example.com"
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "email": new_email
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email
    assert data["username"] == authenticated_user["username"]  # Unchanged


def test_update_profile_username_only(client, authenticated_user):
    """Test updating only username"""
    new_username = f"newusername_{str(uuid.uuid4())[:8]}"
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "username": new_username
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == new_username
    assert data["email"] == authenticated_user["email"]  # Unchanged


def test_update_profile_no_fields(client, authenticated_user):
    """Test updating profile with no fields returns error"""
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={}
    )
    
    assert response.status_code == 400
    assert "No fields provided" in response.json()["detail"]


def test_update_profile_duplicate_email(client, authenticated_user):
    """Test updating profile with already existing email"""
    # Create another user
    client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "username": "existinguser",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "first_name": "Existing",
            "last_name": "User"
        }
    )
    
    # Try to update to existing email
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "email": "existing@example.com"
        }
    )
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_update_profile_duplicate_username(client, authenticated_user):
    """Test updating profile with already existing username"""
    # Create another user
    client.post(
        "/auth/register",
        json={
            "email": "another@example.com",
            "username": "existingusername",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "first_name": "Another",
            "last_name": "User"
        }
    )
    
    # Try to update to existing username
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "username": "existingusername"
        }
    )
    
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


def test_update_profile_same_email(client, authenticated_user):
    """Test updating profile with same email (should succeed)"""
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "email": authenticated_user["email"],
            "first_name": "UpdatedName"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == authenticated_user["email"]
    assert data["first_name"] == "UpdatedName"


def test_update_profile_invalid_email(client, authenticated_user):
    """Test updating profile with invalid email format"""
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "email": "not-an-email"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_update_profile_username_too_short(client, authenticated_user):
    """Test updating profile with username too short"""
    response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "username": "ab"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_update_profile_no_auth(client):
    """Test updating profile without authentication"""
    response = client.put(
        "/users/me/profile",
        json={
            "first_name": "New"
        }
    )
    
    assert response.status_code == 401


# ======================================================================================
# Change Password Tests
# ======================================================================================

def test_change_password_success(client, authenticated_user, db_session):
    """Test successfully changing password"""
    response = client.put(
        "/users/me/password",
        headers=authenticated_user["headers"],
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword456!",
            "confirm_new_password": "NewPassword456!"
        }
    )
    
    assert response.status_code == 200
    assert "Password changed successfully" in response.json()["message"]
    
    # Verify old password no longer works
    old_login = client.post(
        "/auth/token",
        data={
            "username": authenticated_user["username"],
            "password": "Password123!"
        }
    )
    assert old_login.status_code == 401
    
    # Verify new password works
    new_login = client.post(
        "/auth/token",
        data={
            "username": authenticated_user["username"],
            "password": "NewPassword456!"
        }
    )
    assert new_login.status_code == 200


def test_change_password_wrong_current(client, authenticated_user):
    """Test changing password with wrong current password"""
    response = client.put(
        "/users/me/password",
        headers=authenticated_user["headers"],
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword456!",
            "confirm_new_password": "NewPassword456!"
        }
    )
    
    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]


def test_change_password_mismatch(client, authenticated_user):
    """Test changing password with mismatched new passwords"""
    response = client.put(
        "/users/me/password",
        headers=authenticated_user["headers"],
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword456!",
            "confirm_new_password": "DifferentPassword456!"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_change_password_same_as_current(client, authenticated_user):
    """Test changing password to same as current"""
    response = client.put(
        "/users/me/password",
        headers=authenticated_user["headers"],
        json={
            "current_password": "Password123!",
            "new_password": "Password123!",
            "confirm_new_password": "Password123!"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_change_password_weak_password(client, authenticated_user):
    """Test changing to a weak password"""
    response = client.put(
        "/users/me/password",
        headers=authenticated_user["headers"],
        json={
            "current_password": "Password123!",
            "new_password": "weak",
            "confirm_new_password": "weak"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_change_password_no_uppercase(client, authenticated_user):
    """Test changing to password without uppercase"""
    response = client.put(
        "/users/me/password",
        headers=authenticated_user["headers"],
        json={
            "current_password": "Password123!",
            "new_password": "newpassword123!",
            "confirm_new_password": "newpassword123!"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_change_password_no_special_char(client, authenticated_user):
    """Test changing to password without special character"""
    response = client.put(
        "/users/me/password",
        headers=authenticated_user["headers"],
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword456",
            "confirm_new_password": "NewPassword456"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_change_password_no_auth(client):
    """Test changing password without authentication"""
    response = client.put(
        "/users/me/password",
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword456!",
            "confirm_new_password": "NewPassword456!"
        }
    )
    
    assert response.status_code == 401


def test_change_password_updates_timestamp(client, authenticated_user, db_session):
    """Test that changing password updates the updated_at timestamp"""
    # Get original user
    user = db_session.query(User).filter(User.username == authenticated_user["username"]).first()
    original_updated_at = user.updated_at
    
    import time
    time.sleep(0.1)  # Ensure time difference
    
    # Change password
    response = client.put(
        "/users/me/password",
        headers=authenticated_user["headers"],
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword456!",
            "confirm_new_password": "NewPassword456!"
        }
    )
    
    assert response.status_code == 200
    
    # Refresh user from DB
    db_session.refresh(user)
    
    # Verify timestamp updated
    assert user.updated_at > original_updated_at


# ======================================================================================
# Combined Workflow Tests
# ======================================================================================

def test_update_profile_then_login(client, authenticated_user):
    """Test updating username and then logging in with new username"""
    # Update username
    new_username = f"mynewusername_{str(uuid.uuid4())[:8]}"
    update_response = client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "username": new_username
        }
    )
    assert update_response.status_code == 200
    
    # Login with new username
    login_response = client.post(
        "/auth/token",
        data={
            "username": new_username,
            "password": "Password123!"
        }
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_update_email_then_verify_profile(client, authenticated_user):
    """Test updating email and verifying it's reflected in profile"""
    # Update email
    new_email = f"mynewemail_{str(uuid.uuid4())[:8]}@example.com"
    client.put(
        "/users/me/profile",
        headers=authenticated_user["headers"],
        json={
            "email": new_email
        }
    )
    
    # Get profile
    profile_response = client.get(
        "/users/me",
        headers=authenticated_user["headers"]
    )
    
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == new_email
