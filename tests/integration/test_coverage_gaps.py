"""
Tests to cover gaps in jwt.py, redis.py, and main.py for 95% coverage target.
"""
import pytest
import threading
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from faker import Faker
from datetime import timedelta

from app.auth.jwt import (
    create_token, decode_token, get_current_user, 
    get_password_hash, verify_password
)
from app.schemas.token import TokenType
from app.models.user import User
import app.auth.jwt as jwt_mod
import app.auth.redis as redis_mod

fake = Faker()


class _FakeRedis:
    """Fake Redis for testing."""
    def __init__(self):
        self._store = {}

    async def set(self, key: str, value: str, ex: int | None = None):
        self._store[key] = value

    async def exists(self, key: str) -> bool:
        return key in self._store


@pytest.fixture(autouse=True)
def mock_redis_coverage(monkeypatch):
    """Mock Redis functions for coverage gap tests."""
    fake_redis = _FakeRedis()
    _blacklisted = set()

    async def _get():
        return fake_redis

    async def _add_to_blacklist(jti: str, exp: int):
        _blacklisted.add(jti)

    async def _is_blacklisted(jti: str) -> bool:
        return jti in _blacklisted

    monkeypatch.setattr(redis_mod, "get_redis", _get)
    monkeypatch.setattr(redis_mod, "add_to_blacklist", _add_to_blacklist)
    monkeypatch.setattr(redis_mod, "is_blacklisted", _is_blacklisted)
    monkeypatch.setattr(jwt_mod, "is_blacklisted", _is_blacklisted)


def _run(coro):
    """Run async code synchronously using a background thread to avoid nested loops."""
    import asyncio

    result: dict[str, object] = {"value": None, "exc": None}

    def _target():
        try:
            result["value"] = asyncio.run(coro)
        except Exception as exc:  # noqa: BLE001 - re-raise below
            result["exc"] = exc

    thread = threading.Thread(target=_target)
    thread.start()
    thread.join()
    if result["exc"] is not None:
        raise result["exc"]
    return result["value"]


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_get_password_hash(self):
        """Test creating a password hash."""
        plain = "TestPassword123!"
        hashed = get_password_hash(plain)
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != plain
    
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        plain = "TestPassword123!"
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        plain = "TestPassword123!"
        hashed = get_password_hash(plain)
        assert verify_password("WrongPassword", hashed) is False


class TestTokenCreation:
    """Test edge cases in token creation."""
    
    def test_create_token_with_uuid_user_id(self):
        """Test creating token with UUID user_id (not string)."""
        user_id = uuid4()
        token = create_token(user_id, TokenType.ACCESS)
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_token_explicit_expiry_access(self):
        """Test creating access token with explicit expiry."""
        user_id = str(uuid4())
        delta = timedelta(hours=1)
        token = create_token(user_id, TokenType.ACCESS, delta)
        assert token is not None


class TestDecodeTokenEdgeCases:
    """Test edge cases in token decoding."""
    
    def test_decode_malformed_jwt(self):
        """Test decoding completely malformed JWT."""
        with pytest.raises(HTTPException) as exc_info:
            _run(decode_token("not.a.real.token.format", TokenType.ACCESS))
        assert exc_info.value.status_code == 401
    
    def test_decode_with_verify_exp_false(self):
        """Test decoding expired token with verify_exp=False."""
        user_id = str(uuid4())
        token = create_token(user_id, TokenType.ACCESS, timedelta(seconds=-1))
        # This should still work because verify_exp=False skips expiration check
        payload = _run(decode_token(token, TokenType.ACCESS, verify_exp=False))
        assert payload["sub"] == user_id


class TestGetCurrentUserErrorHandling:
    """Test error handling in get_current_user."""
    
    def test_get_current_user_invalid_token(self, db_session: Session):
        """Test get_current_user with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            _run(get_current_user(token="invalid.token.format", db=db_session))
        assert exc_info.value.status_code == 401
    
    def test_get_current_user_exception_handling(self, db_session: Session, monkeypatch):
        """Test get_current_user exception handling when decode_token raises."""
        user_id = str(uuid4())
        token = create_token(user_id, TokenType.ACCESS, timedelta(seconds=-1))
        
        # Intentionally pass an expired token to trigger exception path
        with pytest.raises(HTTPException) as exc_info:
            _run(get_current_user(token=token, db=db_session))
        assert exc_info.value.status_code == 401


class TestRefreshTokenFlow:
    """Test refresh token creation and validation."""
    
    def test_refresh_token_cannot_be_used_as_access(self):
        """Test that refresh token cannot be decoded as access token."""
        user_id = str(uuid4())
        refresh_token = create_token(user_id, TokenType.REFRESH)
        
        with pytest.raises(HTTPException) as exc_info:
            _run(decode_token(refresh_token, TokenType.ACCESS))
        assert exc_info.value.status_code == 401
    
    def test_access_token_cannot_be_used_as_refresh(self):
        """Test that access token cannot be decoded as refresh token."""
        user_id = str(uuid4())
        access_token = create_token(user_id, TokenType.ACCESS)
        
        with pytest.raises(HTTPException) as exc_info:
            _run(decode_token(access_token, TokenType.REFRESH))
        assert exc_info.value.status_code == 401


class TestUserActiveStatus:
    """Test user active/inactive status checks."""
    
    def test_get_current_user_deleted_user(self, db_session: Session):
        """Test get_current_user when user was deleted."""
        user_id = str(uuid4())
        token = create_token(user_id, TokenType.ACCESS)
        
        with pytest.raises(HTTPException) as exc_info:
            _run(get_current_user(token=token, db=db_session))
        # get_current_user catches HTTPException and re-raises with 401
        assert exc_info.value.status_code == 401
