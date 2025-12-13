"""Additional JWT branch coverage tests."""
import asyncio
import threading
import pytest

from app.auth.jwt import create_token, decode_token, get_current_user
from app.schemas.token import TokenType
from app.auth import jwt as jwt_mod
from fastapi import HTTPException
from uuid import uuid4
from sqlalchemy.orm import Session
from jose import JWTError


def _run(coro):
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


def test_invalid_token_type_branch():
    user_id = str(uuid4())
    refresh_token = create_token(user_id, TokenType.REFRESH)
    with pytest.raises(HTTPException) as exc_info:
        _run(decode_token(refresh_token, TokenType.ACCESS))
    assert exc_info.value.status_code == 401


def test_jwt_error_branch():
    bad_token = "not-a-valid-jwt"
    with pytest.raises(HTTPException) as exc_info:
        _run(decode_token(bad_token, TokenType.ACCESS))
    assert exc_info.value.status_code == 401


def test_decode_token_jwterror(monkeypatch):
    token = create_token(str(uuid4()), TokenType.ACCESS)

    def fake_decode(*args, **kwargs):
        raise JWTError("bad")

    monkeypatch.setattr(jwt_mod.jwt, "decode", fake_decode)

    with pytest.raises(HTTPException) as exc_info:
        _run(decode_token(token, TokenType.ACCESS))
    assert exc_info.value.status_code == 401


def test_get_current_user_wraps_exceptions(db_session: Session, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(jwt_mod, "decode_token", boom)
    token = "whatever"
    with pytest.raises(HTTPException) as exc_info:
        _run(get_current_user(token=token, db=db_session))
    assert exc_info.value.status_code == 401
    assert "boom" in str(exc_info.value.detail)
