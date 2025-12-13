"""Targeted tests to cover main.py edge cases and redis fallback."""
import asyncio
import threading
import types
import sys
from uuid import uuid4
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.redis import get_redis, add_to_blacklist, is_blacklisted
from app.auth import redis as redis_module
from app.auth.jwt import create_token
from app.schemas.token import TokenType
from app.models.user import User
from app.models.calculation import Calculation
from app.database import get_db

# ---------------------------------------------------------------------------
# Async runner helper (threaded) to avoid nested loop issues
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Redis coverage: fallback and aioredis branch
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_redis_cache():
    if hasattr(get_redis, "redis"):
        delattr(get_redis, "redis")
    yield
    if hasattr(get_redis, "redis"):
        delattr(get_redis, "redis")


def test_get_redis_fallback(monkeypatch):
    """When aioredis import fails, fallback memory store is used."""
    monkeypatch.delitem(sys.modules, "aioredis", raising=False)
    redis = _run(get_redis())
    _run(add_to_blacklist("jti-fallback", 60))
    assert _run(is_blacklisted("jti-fallback")) is True
    # ensure the object is the in-memory fake (has _store attr)
    assert hasattr(redis, "_store")


def test_get_redis_aioredis_stub(monkeypatch):
    """When aioredis is available, from_url is called and cached."""
    class _DummyClient:
        def __init__(self):
            self.set_calls = []
            self.exists_calls = []

        async def set(self, key, value, ex=None):
            self.set_calls.append((key, value, ex))

        async def exists(self, key):
            self.exists_calls.append(key)
            return False

    async def _from_url(url):
        return _DummyClient()

    dummy_module = types.SimpleNamespace(from_url=_from_url)
    monkeypatch.setitem(sys.modules, "aioredis", dummy_module)

    client1 = _run(get_redis())
    client2 = _run(get_redis())
    assert client1 is client2  # cached
    assert isinstance(client1, _DummyClient)
    _run(add_to_blacklist("jti-stub", 10))
    assert _run(is_blacklisted("jti-stub")) is False  # exists returns False
    assert client1.set_calls  # ensure set was invoked


# ---------------------------------------------------------------------------
# Main API coverage for error branches
# ---------------------------------------------------------------------------

@pytest.fixture
def client(db_session):
    """TestClient with overridden dependencies for auth and DB."""
    test_user = User.register(db_session, {
        "username": f"user-{uuid4().hex[:8]}",
        "email": f"{uuid4().hex}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "Passw0rd!",
    })
    db_session.commit()
    db_session.refresh(test_user)

    # Expose the created test user on the TestClient
    app.test_user = test_user  # type: ignore[attr-defined]

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.rollback()

    async def override_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    from app.auth.dependencies import get_current_active_user
    app.dependency_overrides[get_current_active_user] = override_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_get_calculation_invalid_id(client):
    resp = client.get("/calculations/not-a-uuid")
    assert resp.status_code == 400
    assert "invalid calculation id" in resp.text.lower()


def test_get_calculation_not_found(client):
    resp = client.get(f"/calculations/{uuid4()}")
    assert resp.status_code == 404


def test_update_calculation_invalid_id(client):
    resp = client.put("/calculations/not-a-uuid", json={"inputs": [1, 2]})
    assert resp.status_code == 400


def test_update_calculation_not_found(client):
    resp = client.put(f"/calculations/{uuid4()}", json={"inputs": [1, 2]})
    assert resp.status_code == 404


def test_delete_calculation_invalid_id(client):
    resp = client.delete("/calculations/not-a-uuid")
    assert resp.status_code == 400


def test_delete_calculation_not_found(client):
    resp = client.delete(f"/calculations/{uuid4()}")
    assert resp.status_code == 404


def test_create_list_and_get_calculation(client):
    create_resp = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [1, 2]},
    )
    assert create_resp.status_code == 201
    calc = create_resp.json()

    list_resp = client.get("/calculations")
    assert list_resp.status_code == 200
    assert any(item["id"] == calc["id"] for item in list_resp.json())

    get_resp = client.get(f"/calculations/{calc['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["result"] == 3


def test_update_and_delete_calculation_success(client):
    create_resp = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [2, 3]},
    )
    calc_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/calculations/{calc_id}", json={"inputs": [5, 7]}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["result"] == 12

    delete_resp = client.delete(f"/calculations/{calc_id}")
    assert delete_resp.status_code == 204


def test_login_form_success(client):
    user = app.test_user  # type: ignore[attr-defined]
    resp = client.post(
        "/auth/token",
        data={"username": user.username, "password": "Passw0rd!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"


def test_login_json_success(client):
    user = app.test_user  # type: ignore[attr-defined]
    resp = client.post(
        "/auth/login",
        json={"username": user.username, "password": "Passw0rd!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"


def test_login_json_naive_expiry(monkeypatch, client):
    user = app.test_user  # type: ignore[attr-defined]

    def fake_auth(db, username, password):
        return {
            "user": user,
            "access_token": "token",
            "refresh_token": "rtoken",
            "expires_at": datetime.utcnow(),  # naive datetime triggers tzinfo branch
        }

    monkeypatch.setattr(User, "authenticate", staticmethod(fake_auth))
    resp = client.post(
        "/auth/login",
        json={"username": user.username, "password": "whatever"},
    )
    assert resp.status_code == 200


def test_login_form_invalid(monkeypatch, client):
    monkeypatch.setattr(User, "authenticate", staticmethod(lambda db, u, p: None))
    resp = client.post(
        "/auth/token",
        data={"username": "bad", "password": "bad"},
    )
    assert resp.status_code == 401


def test_web_routes():
    with TestClient(app) as c:
        for path in ["/", "/login", "/register", "/dashboard", "/dashboard/view/123", "/dashboard/edit/123"]:
            r = c.get(path)
            assert r.status_code == 200
        health = c.get("/health")
        assert health.status_code == 200
