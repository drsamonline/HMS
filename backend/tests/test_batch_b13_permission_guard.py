"""Gate tests for build-plan batch B13: the guard and default deny.

Built on a small application rather than the real one, deliberately: the subject
is the mechanism, and the real app has 242 routes that B14 has not guarded yet.
Testing the mechanism in isolation is what makes the B14 failure meaningful - when
a real route returns 403 there, it is the guard working, not the test rig.
"""

from __future__ import annotations

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.jwt import create_access_token
from app.core.permissions import CODES
from app.dependencies.permissions import (
    PERMISSION_MARKER,
    default_deny,
    permissions_for_user,
    require,
    route_permission,
)


@pytest.fixture()
def seeded(tmp_path, monkeypatch):
    """A database with two users: one who may read patients, one who may not."""

    import asyncio

    import app.models  # noqa: F401
    from app.db.base import Base
    from app.db import session as session_module
    from app.config import settings as settings_module

    database = tmp_path / "hhms-b13.sqlite3"
    monkeypatch.setenv(
        "DATABASE_URL", f"sqlite+aiosqlite:///{database.as_posix()}"
    )
    monkeypatch.setenv("ENVIRONMENT", "test")
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    engine = create_async_engine(f"sqlite+aiosqlite:///{database.as_posix()}")

    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.role_permission import RolePermission
    from app.models.user import User
    from app.models.user_role import UserRole

    async def _seed() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as db:
            read_patients = Permission(
                name="View patients", code="patients.read", module="patients"
            )
            read_stock = Permission(
                name="View stock", code="inventory.read", module="inventory"
            )
            doctor = Role(role_name="medical officer", description="doctor")
            keeper = Role(role_name="store keeper", description="stores")
            alice = User(
                username="alice",
                password_hash="x",
                full_name="Alice",
                is_active=True,
            )
            bob = User(
                username="bob", password_hash="x", full_name="Bob", is_active=True
            )
            db.add_all([read_patients, read_stock, doctor, keeper, alice, bob])
            await db.flush()
            db.add_all([
                RolePermission(role_id=doctor.id, permission_id=read_patients.id),
                RolePermission(role_id=keeper.id, permission_id=read_stock.id),
                UserRole(user_id=alice.id, role_id=doctor.id),
                UserRole(user_id=bob.id, role_id=keeper.id),
            ])
            await db.commit()
            ids = {"alice": alice.id, "bob": bob.id}

        async with factory() as db:
            ids["alice_codes"] = await permissions_for_user(db, ids["alice"])
            ids["bob_codes"] = await permissions_for_user(db, ids["bob"])

        return ids

    loop = asyncio.new_event_loop()
    try:
        ids = loop.run_until_complete(_seed())
    finally:
        loop.close()

    yield ids

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _app(mode: str, monkeypatch) -> TestClient:
    monkeypatch.setenv("PERMISSION_ENFORCEMENT", mode)
    from app.config.settings import get_settings

    get_settings.cache_clear()

    application = FastAPI()
    router = APIRouter(prefix="/api/v1", dependencies=[Depends(default_deny)])

    @router.get("/unguarded")
    async def unguarded() -> dict:
        return {"ok": True}

    @router.get("/guarded", dependencies=[Depends(require("patients.read"))])
    async def guarded() -> dict:
        return {"ok": True}

    @router.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    application.include_router(router)
    return TestClient(application)


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


# ------------------------------------------------------------------ resolution
def test_permissions_come_from_roles(seeded) -> None:
    assert "patients.read" in seeded["alice_codes"]
    assert "inventory.read" not in seeded["alice_codes"]
    assert "inventory.read" in seeded["bob_codes"]
    assert "patients.read" not in seeded["bob_codes"]


# ----------------------------------------------------------------------- guard
def test_guarded_route_allows_the_holder(seeded, monkeypatch) -> None:
    client = _app("enforce", monkeypatch)
    response = client.get("/api/v1/guarded", headers=_token(seeded["alice"]))
    assert response.status_code == 200, response.text


def test_guarded_route_refuses_a_non_holder(seeded, monkeypatch) -> None:
    client = _app("enforce", monkeypatch)
    response = client.get("/api/v1/guarded", headers=_token(seeded["bob"]))
    assert response.status_code == 403, response.text
    assert "patients.read" in response.json()["detail"]


def test_guarded_route_refuses_an_anonymous_caller(seeded, monkeypatch) -> None:
    client = _app("enforce", monkeypatch)
    assert client.get("/api/v1/guarded").status_code == 401


# ---------------------------------------------------------------- default deny
def test_unguarded_route_is_refused_under_enforce(seeded, monkeypatch) -> None:
    client = _app("enforce", monkeypatch)
    response = client.get("/api/v1/unguarded", headers=_token(seeded["alice"]))
    assert response.status_code == 403, response.text
    assert "no permission guard" in response.json()["detail"]


def test_unguarded_route_is_allowed_under_warn(seeded, monkeypatch) -> None:
    """The staged mode: log it, allow it, so the suite stays green during B14."""
    client = _app("warn", monkeypatch)
    response = client.get("/api/v1/unguarded", headers=_token(seeded["alice"]))
    assert response.status_code == 200, response.text


def test_explicit_guards_apply_even_under_warn(seeded, monkeypatch) -> None:
    """warn softens default deny; it does not soften a declared guard."""
    client = _app("warn", monkeypatch)
    response = client.get("/api/v1/guarded", headers=_token(seeded["bob"]))
    assert response.status_code == 403, response.text


def test_public_path_is_reachable_without_a_guard(seeded, monkeypatch) -> None:
    client = _app("enforce", monkeypatch)
    assert client.get("/api/v1/health").status_code == 200


# ------------------------------------------------------------------- mechanics
def test_require_rejects_an_undeclared_code() -> None:
    with pytest.raises(ValueError, match="unknown permission code"):
        require("patients.destroy")


def test_require_stamps_the_code_on_the_dependency() -> None:
    guard = require("billing.void")
    assert getattr(guard, PERMISSION_MARKER) == "billing.void"


def test_route_permission_finds_the_declared_code(seeded, monkeypatch) -> None:
    client = _app("enforce", monkeypatch)
    routes = {route.path: route for route in client.app.routes}
    assert route_permission(routes["/api/v1/guarded"]) == "patients.read"
    assert route_permission(routes["/api/v1/unguarded"]) is None


def test_every_declared_code_is_valid() -> None:
    """A guard built from a catalogue code must never raise at import."""
    for code in CODES:
        assert getattr(require(code), PERMISSION_MARKER) == code
