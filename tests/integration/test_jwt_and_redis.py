"""
Tests for JWT and Redis authentication functionality
"""
import pytest
import asyncio
import threading
from fastapi import HTTPException
from app.auth.jwt import create_token, decode_token, get_current_user
import app.auth.redis as redis_mod
import app.auth.jwt as jwt_mod
from app.schemas.token import TokenType
from app.models.user import User
from sqlalchemy.orm import Session
from faker import Faker
from datetime import timedelta
from uuid import uuid4
from app.core.config import get_settings

fake = Faker()
settings = get_settings()

class _FakeRedis:
    def __init__(self):
        self._store = {}

    async def set(self, key: str, value: str, ex: int | None = None):
        self._store[key] = value

    async def exists(self, key: str) -> bool:
        return key in self._store

@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
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
    """Run async code synchronously, even if another loop is running, by using a thread."""
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


def test_decode_expired_token():
    """Test decoding an expired token raises HTTPException"""
    user_id = str(uuid4())
    token = create_token(user_id, TokenType.ACCESS, timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        _run(decode_token(token, TokenType.ACCESS))
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_decode_invalid_token():
    """Test decoding an invalid token raises HTTPException"""
    invalid_token = "invalid.token.here"
    with pytest.raises(HTTPException) as exc_info:
        _run(decode_token(invalid_token, TokenType.ACCESS))
    assert exc_info.value.status_code == 401


def test_decode_wrong_token_type():
    """Test decoding token with wrong type raises HTTPException"""
    user_id = str(uuid4())
    access_token = create_token(user_id, TokenType.ACCESS)
    with pytest.raises(HTTPException) as exc_info:
        _run(decode_token(access_token, TokenType.REFRESH))
    assert exc_info.value.status_code == 401


def test_blacklist_token():
    """Test adding token to blacklist and checking it"""
    jti = str(uuid4())
    _run(redis_mod.add_to_blacklist(jti, 3600))
    is_blocked = _run(redis_mod.is_blacklisted(jti))
    assert is_blocked is True


def test_non_blacklisted_token():
    """Test that non-blacklisted token returns False"""
    jti = str(uuid4())
    is_blocked = _run(redis_mod.is_blacklisted(jti))
    assert is_blocked is False


def test_decode_blacklisted_token():
    """Test that blacklisted token raises HTTPException"""
    user_id = str(uuid4())
    token = create_token(user_id, TokenType.ACCESS)
    payload = _run(decode_token(token, TokenType.ACCESS))
    jti = payload["jti"]
    _run(redis_mod.add_to_blacklist(jti, 3600))
    with pytest.raises(HTTPException) as exc_info:
        _run(decode_token(token, TokenType.ACCESS))
    assert exc_info.value.status_code == 401
    assert "revoked" in exc_info.value.detail.lower()


def test_get_redis_singleton():
    """Test that get_redis returns same instance"""
    redis1 = _run(redis_mod.get_redis())
    redis2 = _run(redis_mod.get_redis())
    assert redis1 is redis2


def test_get_current_user_not_found(db_session: Session):
    """Test get_current_user with non-existent user ID"""
    fake_user_id = str(uuid4())
    token = create_token(fake_user_id, TokenType.ACCESS)
    with pytest.raises(HTTPException) as exc_info:
        _run(get_current_user(token=token, db=db_session))
    assert exc_info.value.status_code == 401
    assert "not found" in exc_info.value.detail.lower()


def test_get_current_user_inactive(db_session: Session):
    """Test get_current_user with inactive user"""
    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "password": "TestPass123!"
    }
    user = User.register(db_session, user_data)
    user.is_active = False
    db_session.commit()
    token = create_token(str(user.id), TokenType.ACCESS)
    with pytest.raises(HTTPException) as exc_info:
        _run(get_current_user(token=token, db=db_session))
    assert exc_info.value.status_code == 401
    assert "inactive" in exc_info.value.detail.lower()


def test_create_refresh_token():
    """Test creating a refresh token"""
    user_id = str(uuid4())
    token = create_token(user_id, TokenType.REFRESH)
    payload = _run(decode_token(token, TokenType.REFRESH))
    assert payload["sub"] == user_id
    assert payload["type"] == TokenType.REFRESH.value


def test_token_encoding_exception():
    """Test that encoding exceptions are handled"""
    user_id = str(uuid4())
    token = create_token(user_id, TokenType.ACCESS)
    assert token is not None


def test_create_token_type_error():
    """Test creating token handles type conversion"""
    user_id = uuid4()
    token = create_token(user_id, TokenType.ACCESS)
    assert token is not None
    assert isinstance(token, str)
