"""Gate tests for build-plan batch B15a: resolve permissions once per request.

B14 put a join behind every guarded route. A request that touches a list, a
detail and a write paid for it three times, and the suite - two thousand requests
- went from 290 seconds to over 450.

The memo is per request, not global: a revoked role must stop working on the next
request, not when a cache expires. Both halves of that are tested here, because a
cache that is too eager is a security bug and a cache that does nothing is a
performance bug that looks like a fix.
"""

from __future__ import annotations

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.jwt import create_access_token
from app.dependencies import permissions as permissions_module
from app.dependencies.permissions import default_deny, require


@pytest.fixture()
def seeded(tmp_path, monkeypatch):
    """One user, one role holding patients.read."""

    import asyncio

    import app.models  # noqa: F401
    from app.config import settings as settings_module
    from app.db import session as session_module
    from app.db.base import Base
    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.role_permission import RolePermission
    from app.models.user import User
    from app.models.user_role import UserRole

    database = tmp_path / "hhms-b15a.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database.as_posix()}")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("PERMISSION_ENFORCEMENT", "enforce")
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    engine = create_async_engine(f"sqlite+aiosqlite:///{database.as_posix()}")

    async def _seed() -> int:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as db:
            permission = Permission(
                name="View patients", code="patients.read", module="patients"
            )
            role = Role(role_name="medical officer", description="doctor")
            user = User(
                username="alice", password_hash="x", full_name="Alice", is_active=True
            )
            db.add_all([permission, role, user])
            await db.flush()
            db.add_all([
                RolePermission(role_id=role.id, permission_id=permission.id),
                UserRole(user_id=user.id, role_id=role.id),
            ])
            await db.commit()
            return user.id

    loop = asyncio.new_event_loop()
    try:
        user_id = loop.run_until_complete(_seed())
    finally:
        loop.close()

    yield user_id

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _client() -> TestClient:
    """A route guarded three times over: the worst case for a naive guard."""

    application = FastAPI()
    router = APIRouter(prefix="/api/v1", dependencies=[Depends(default_deny)])

    @router.get(
        "/triple",
        dependencies=[
            Depends(require("patients.read")),
            Depends(require("patients.read")),
        ],
    )
    async def triple() -> dict:
        return {"ok": True}

    @router.get("/single", dependencies=[Depends(require("patients.read"))])
    async def single() -> dict:
        return {"ok": True}

    application.include_router(router)
    return TestClient(application)


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


def test_permissions_are_resolved_once_per_request(seeded, monkeypatch) -> None:
    """Two guards on one route must not mean two joins."""

    calls = {"n": 0}
    real = permissions_module.permissions_for_user

    async def counting(db, user_id):
        calls["n"] += 1
        return await real(db, user_id)

    monkeypatch.setattr(permissions_module, "permissions_for_user", counting)

    client = _client()
    response = client.get("/api/v1/triple", headers=_token(seeded))
    assert response.status_code == 200, response.text
    assert calls["n"] == 1, f"resolved {calls['n']} times for one request"


def test_the_memo_does_not_survive_the_request(seeded, monkeypatch) -> None:
    """A revoked role must stop working on the next request, not at cache expiry."""

    calls = {"n": 0}
    real = permissions_module.permissions_for_user

    async def counting(db, user_id):
        calls["n"] += 1
        return await real(db, user_id)

    monkeypatch.setattr(permissions_module, "permissions_for_user", counting)

    client = _client()
    for _ in range(3):
        assert client.get("/api/v1/single", headers=_token(seeded)).status_code == 200

    assert calls["n"] == 3, (
        f"resolved {calls['n']} times across three requests; the memo leaked "
        "between them, which would keep a revoked role alive"
    )


def test_a_request_without_a_guard_still_resolves_nothing(seeded, monkeypatch) -> None:
    calls = {"n": 0}
    real = permissions_module.permissions_for_user

    async def counting(db, user_id):
        calls["n"] += 1
        return await real(db, user_id)

    monkeypatch.setattr(permissions_module, "permissions_for_user", counting)

    application = FastAPI()
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    application.include_router(router)
    client = TestClient(application)

    assert client.get("/api/v1/health").status_code == 200
    assert calls["n"] == 0


def test_the_guard_still_refuses(seeded, monkeypatch) -> None:
    """Memoisation must not soften the decision it is caching."""

    client = _client()
    # A subject with no user behind it holds nothing.
    response = client.get(
        "/api/v1/single",
        headers={"Authorization": f"Bearer {create_access_token(subject='424242')}"},
    )
    assert response.status_code == 403, response.text
