"""Gate tests for build-plan batch B34: the pharmacovigilance register.

NCH Code of Ethics 37 requires adverse events to homoeopathic products to be
reported. The register keeps two moments - when the event happened and when it was
reported - because the gap between them is what a hospital is asked to evidence.

The property that matters most: the readiness report must stop saying this duty is
unimplemented, and must start counting.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.models.patient import Patient


@pytest.fixture()
def session(tmp_path, monkeypatch):
    from app.config import settings as settings_module
    from app.db import session as session_module
    from app.db.base import Base

    path = tmp_path / "hhms-b34.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{path.as_posix()}")
    monkeypatch.setenv("ENVIRONMENT", "test")
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _seed():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with factory() as db:
            now = datetime.now(UTC)
            patient = Patient(
                patient_number="P-0001",
                first_name="Asha",
                last_name="Patel",
                gender="female",
                registration_date=now,
                created_at=now,
                updated_at=now,
            )
            db.add(patient)
            await db.commit()
            return patient.id

    loop = asyncio.new_event_loop()
    try:
        patient_id = loop.run_until_complete(_seed())
    finally:
        loop.close()

    yield factory, patient_id

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _event(patient_id: int, **overrides):
    base = {
        "patient_id": patient_id,
        "product_name": "Arnica Montana 30C",
        "event_datetime": datetime.now(UTC),
        "severity": "moderate",
        "description": "Generalised rash within two hours of the dose.",
        "recorded_by": 1,
    }
    base.update(overrides)
    return base


# ------------------------------------------------------------------ recording
def test_an_event_is_recorded_unreported(session) -> None:
    from app.services import adverse_events

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            event = await adverse_events.record(db, **_event(patient_id))
            await db.commit()
            return event.reported, event.reported_at

    reported, reported_at = _run(_go())
    assert reported is False, "recording is not reporting"
    assert reported_at is None


def test_an_event_needs_a_description(session) -> None:
    from app.core.exceptions import BusinessRuleException
    from app.services import adverse_events

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            await adverse_events.record(db, **_event(patient_id, description="  "))

    with pytest.raises(BusinessRuleException, match="needs a description"):
        _run(_go())


def test_severity_must_be_one_of_the_three(session) -> None:
    from app.core.exceptions import BusinessRuleException
    from app.services import adverse_events

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            await adverse_events.record(db, **_event(patient_id, severity="catastrophic"))

    with pytest.raises(BusinessRuleException, match="Severity must be one of"):
        _run(_go())


def test_an_unknown_patient_is_refused(session) -> None:
    from app.core.exceptions import ResourceNotFoundException
    from app.services import adverse_events

    factory, _patient_id = session

    async def _go():
        async with factory() as db:
            await adverse_events.record(db, **_event(9999))

    with pytest.raises(ResourceNotFoundException):
        _run(_go())


# ------------------------------------------------------------------ reporting
def test_reporting_records_the_second_moment(session) -> None:
    from app.services import adverse_events

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            event = await adverse_events.record(db, **_event(patient_id))
            await db.commit()
            reported = await adverse_events.mark_reported(
                db, event_id=event.id, reported_to="CCRH pharmacovigilance cell", reported_by=1
            )
            await db.commit()
            return reported.reported, reported.reported_at, reported.reported_to

    reported, reported_at, reported_to = _run(_go())
    assert reported is True
    assert reported_at is not None
    assert reported_to == "CCRH pharmacovigilance cell"


def test_reporting_twice_keeps_the_first_date(session) -> None:
    """A second date would make one event look like two."""

    from app.services import adverse_events

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            event = await adverse_events.record(db, **_event(patient_id))
            await db.commit()
            first = await adverse_events.mark_reported(
                db, event_id=event.id, reported_to="CCRH", reported_by=1
            )
            await db.commit()
            first_at = first.reported_at
            second = await adverse_events.mark_reported(
                db, event_id=event.id, reported_to="Somewhere else", reported_by=2
            )
            await db.commit()
            return first_at, second.reported_at, second.reported_to

    first_at, second_at, reported_to = _run(_go())
    assert second_at == first_at
    assert reported_to == "CCRH"


def test_reporting_needs_a_recipient(session) -> None:
    from app.core.exceptions import BusinessRuleException
    from app.services import adverse_events

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            event = await adverse_events.record(db, **_event(patient_id))
            await db.commit()
            await adverse_events.mark_reported(
                db, event_id=event.id, reported_to=" ", reported_by=1
            )

    with pytest.raises(BusinessRuleException, match="who the event was reported to"):
        _run(_go())


# ------------------------------------------------------- the readiness report
def test_readiness_no_longer_says_the_duty_is_unimplemented(session) -> None:
    from app.services import nch_compliance

    factory, _patient_id = session

    async def _go():
        async with factory() as db:
            return await nch_compliance.readiness(db)

    adverse = _run(_go())["adverse_event_register"]
    assert "Not implemented yet" not in (adverse["note"] or "")
    assert adverse["ok"] is True
    assert adverse["missing_count"] == 0


def test_readiness_counts_an_unreported_event(session) -> None:
    from app.services import adverse_events, nch_compliance

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            await adverse_events.record(db, **_event(patient_id))
            await db.commit()
            return await nch_compliance.readiness(db)

    adverse = _run(_go())["adverse_event_register"]
    assert adverse["ok"] is False
    assert adverse["missing_count"] == 1


def test_reporting_the_event_clears_the_readiness_gap(session) -> None:
    from app.services import adverse_events, nch_compliance

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            event = await adverse_events.record(db, **_event(patient_id))
            await db.commit()
            await adverse_events.mark_reported(
                db, event_id=event.id, reported_to="CCRH", reported_by=1
            )
            await db.commit()
            return await nch_compliance.readiness(db)

    assert _run(_go())["adverse_event_register"]["ok"] is True
