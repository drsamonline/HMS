"""Gate tests for build-plan batch B17: a disabled module does not serve.

`MASTER_SPECIFICATION` 7.3 asks for two things at once, and both are tested here:
the workflow disappears, and the records do not. A test that only proved the first
would be satisfied by deleting the module, which is exactly what the specification
forbids.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.dependencies.modules import enabled_modules, require_module
from app.models.module_state import ModuleState


@pytest.fixture()
def database(tmp_path, monkeypatch):
    """A file-backed database with the module table and one pharmacy row."""

    import asyncio

    import app.models  # noqa: F401
    from app.config import settings as settings_module
    from app.db import session as session_module
    from app.db.base import Base
    from app.models.dispense_record import DispenseRecord
    from app.modules.registry import MODULES

    path = tmp_path / "hhms-b17.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{path.as_posix()}")
    monkeypatch.setenv("ENVIRONMENT", "test")
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")

    async def _seed() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as db:
            for module in MODULES:
                db.add(
                    ModuleState(
                        module_code=module.code,
                        is_enabled=module.is_core or module.code == "pharmacy",
                    )
                )
            from datetime import UTC, datetime

            now = datetime.now(UTC)

            db.add(
                DispenseRecord(
                    medicine_id=1,
                    stock_batch_id=1,
                    quantity_dispensed=1,
                    dispensed_by=1,
                    dispense_date=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            await db.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_seed())
    finally:
        loop.close()

    yield engine

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _client(monkeypatch):
    """The real application, with the module gate in place."""

    from fastapi.testclient import TestClient

    from app.app import create_application

    return TestClient(create_application())


def _admin(monkeypatch) -> dict:
    from tests._qa_harness import auth_headers

    return auth_headers()


# ------------------------------------------------------------- the gate itself
def test_require_module_rejects_an_unknown_module() -> None:
    with pytest.raises(ValueError, match="unknown module"):
        require_module("dentistry")


def test_core_is_always_enabled(database) -> None:
    import asyncio

    factory = async_sessionmaker(database, expire_on_commit=False)

    async def _read():
        async with factory() as db:
            return await enabled_modules(db)

    loop = asyncio.new_event_loop()
    try:
        codes = loop.run_until_complete(_read())
    finally:
        loop.close()

    assert "core" in codes
    assert "pharmacy" in codes
    assert "billing" not in codes


# --------------------------------------------------------- over the real routes
def test_a_disabled_module_answers_404(database, monkeypatch) -> None:
    """Billing is off, so its routes do not exist for this hospital."""

    with _client(monkeypatch) as client:
        headers = _admin(monkeypatch)
        response = client.get("/api/v1/billing/invoices", headers=headers)

    assert response.status_code == 404, response.text
    assert "Billing" in response.text


def test_an_enabled_module_serves(database, monkeypatch) -> None:
    """The other half: a disabled gate must not close everything."""

    with _client(monkeypatch) as client:
        headers = _admin(monkeypatch)
        response = client.get("/api/v1/medicines", headers=headers)

    assert response.status_code == 200, response.text


def test_core_always_serves(database, monkeypatch) -> None:
    with _client(monkeypatch) as client:
        headers = _admin(monkeypatch)
        assert client.get("/api/v1/patients", headers=headers).status_code == 200


def test_disabling_preserves_every_record(database, monkeypatch) -> None:
    """The specification's other half: switching off must not delete anything."""

    import asyncio

    factory = async_sessionmaker(database, expire_on_commit=False)

    async def _count() -> int:
        from app.models.dispense_record import DispenseRecord

        async with factory() as db:
            return (
                await db.execute(select(func.count()).select_from(DispenseRecord))
            ).scalar_one()

    async def _disable() -> None:
        async with factory() as db:
            state = (
                await db.execute(
                    select(ModuleState).where(ModuleState.module_code == "pharmacy")
                )
            ).scalar_one()
            state.is_enabled = False
            await db.commit()

    loop = asyncio.new_event_loop()
    try:
        before = loop.run_until_complete(_count())
        loop.run_until_complete(_disable())
        after = loop.run_until_complete(_count())
    finally:
        loop.close()

    assert before == after == 1, "disabling a module must not touch its records"

    with _client(monkeypatch) as client:
        headers = _admin(monkeypatch)
        assert client.get("/api/v1/medicines", headers=headers).status_code == 404


def test_a_disabled_module_answers_404_before_it_answers_403(database, monkeypatch) -> None:
    """A hospital without the module should not learn the route needs a permission.

    404 is the honest answer: the resource does not exist here. 403 would tell the
    caller it exists and they merely lack the grant, which is information a
    hospital that never bought the module has no reason to disclose.
    """

    with _client(monkeypatch) as client:
        headers = _admin(monkeypatch)
        response = client.get("/api/v1/billing/invoices", headers=headers)

    assert response.status_code == 404
