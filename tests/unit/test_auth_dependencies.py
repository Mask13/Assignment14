import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_current_active_user
from app.models.user import User


def create_user_and_token(db: Session, username: str = "testuser", password: str = "StrongPass1"):
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"{username}@example.com",
        "username": username,
        "password": password,
    }
    user = User.register(db, data)
    db.commit()
    db.refresh(user)
    token = User.create_access_token({"sub": str(user.id)})
    return user, token


def test_get_current_user_success(db_session: Session):
    user, token = create_user_and_token(db_session)
    resp = get_current_user(token=token, db=db_session)
    assert resp.id == user.id
    assert resp.username == user.username
    assert resp.email == user.email


def test_get_current_user_invalid_token_raises(db_session: Session):
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="invalid.token", db=db_session)
    assert exc.value.status_code == 401


def test_get_current_user_user_not_found_raises(db_session: Session):
    # Create valid token, then delete user to simulate missing user
    user, token = create_user_and_token(db_session, username="ghostuser")
    db_session.delete(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=db_session)
    assert exc.value.status_code == 401


def test_get_current_active_user_active(db_session: Session):
    user, token = create_user_and_token(db_session, username="activeuser")
    current = get_current_user(token=token, db=db_session)
    active = get_current_active_user(current_user=current)
    assert active.id == user.id


def test_get_current_active_user_inactive_raises(db_session: Session):
    user, token = create_user_and_token(db_session, username="inactiveuser")
    # Mark inactive
    user.is_active = False
    db_session.commit()

    current = get_current_user(token=token, db=db_session)
    with pytest.raises(HTTPException) as exc:
        get_current_active_user(current_user=current)
    assert exc.value.status_code == 400
