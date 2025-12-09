import pytest
from fastapi import HTTPException, status
from app.auth.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from sqlalchemy.orm import Session
import uuid

# Create a user for testing purposes
def create_user(db: Session, username: str = None, is_active: bool = True):
    unique_id = str(uuid.uuid4())[:8]
    if not username:
        username = f"user_{unique_id}"
    
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"{username}@example.com",
        "username": username,
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    user = User.register(db, data)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user

# Test get_current_user with valid token and existing user
def test_get_current_user_valid_token_existing_user(db_session: Session):
    user = create_user(db_session)
    token = User.create_access_token({"sub": str(user.id)})
    
    user_response = get_current_user(token=token, db=db_session)
    
    assert user_response.id == user.id
    assert user_response.username == user.username

# Test get_current_user with invalid token
def test_get_current_user_invalid_token(db_session: Session):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalidtoken", db=db_session)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

# Test get_current_active_user with an active user
def test_get_current_active_user_active(db_session: Session):
    user = create_user(db_session, username="active")
    token = User.create_access_token({"sub": str(user.id)})
    
    current_user = get_current_user(token=token, db=db_session)
    active_user = get_current_active_user(current_user=current_user)
    
    assert active_user.id == user.id

# Test get_current_active_user with an inactive user
def test_get_current_active_user_inactive(db_session: Session):
    user = create_user(db_session, username="inactive", is_active=False)
    token = User.create_access_token({"sub": str(user.id)})
    
    current_user = get_current_user(token=token, db=db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(current_user=current_user)
        
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
