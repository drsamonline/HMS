"""Gate tests for build-plan batch B35: the certificate register.

Two duties. Regulation 7(1) keeps a copy of every medical certificate for at least
three years; regulation 27 requires a written case statement with a referral.

The property worth testing hardest is the retention date: it is computed at issue
and stored, so a later settings change cannot shorten an obligation already made.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.models.patient import Patient


@pytest.fixture()
def session(tmp_path, monkeypatch):
    from app.config import settings as settings_module
    from app.db import session as session_module
    from app.db.base import Base

    path = tmp_path / "hhms-b35.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{path.as_posix()}")
    monkeypatch.setenv("ENVIRONMENT", "test")
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _seed() -> int:
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


def _certificate(patient_id: int, **overrides):
    base = {
        "patient_id": patient_id,
        "certificate_type": "medical",
        "certificate_number": "CERT-0001",
        "content": "Suffering from acute migraine; unfit for duty for three days.",
        "issued_by": 1,
    }
    base.update(overrides)
    return base


# ------------------------------------------------------------------- issuing
def test_a_certificate_is_stored_with_its_retention_date(session) -> None:
    """Regulation 7(1), computed at issue rather than looked up later."""

    from app.services import certificates

    factory, patient_id = session
    issued = datetime(2026, 3, 1, tzinfo=UTC)

    async def _go():
        async with factory() as db:
            row = await certificates.issue(
                db, **_certificate(patient_id, issued_at=issued)
            )
            await db.commit()
            return row.retention_until

    assert _run(_go()) == datetime(2029, 3, 1, tzinfo=UTC)


def test_a_leap_day_certificate_does_not_crash(session) -> None:
    """29 February plus three years is not a date; it clamps to the 28th."""

    from app.services import certificates

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            row = await certificates.issue(
                db,
                **_certificate(
                    patient_id, issued_at=datetime(2028, 2, 29, tzinfo=UTC)
                ),
            )
            await db.commit()
            return row.retention_until

    assert _run(_go()).day == 28


def test_a_referral_needs_a_case_statement(session) -> None:
    """Regulation 27, enforced where the case is still in front of the doctor."""

    from app.core.exceptions import BusinessRuleException
    from app.services import certificates

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            await certificates.issue(
                db, **_certificate(patient_id, certificate_type="referral")
            )

    with pytest.raises(BusinessRuleException, match="case statement"):
        _run(_go())


def test_a_referral_with_a_case_statement_is_accepted(session) -> None:
    from app.services import certificates

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            row = await certificates.issue(
                db,
                **_certificate(
                    patient_id,
                    certificate_type="referral",
                    case_statement="Chronic migraine, three years; referred for imaging.",
                ),
            )
            await db.commit()
            return row.case_statement

    assert _run(_go()).startswith("Chronic migraine")


def test_a_duplicate_certificate_number_is_refused(session) -> None:
    from app.core.exceptions import DuplicateResourceException
    from app.services import certificates

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            await certificates.issue(db, **_certificate(patient_id))
            await db.commit()
            await certificates.issue(db, **_certificate(patient_id))

    with pytest.raises(DuplicateResourceException):
        _run(_go())


def test_an_empty_certificate_is_refused(session) -> None:
    from app.core.exceptions import BusinessRuleException
    from app.services import certificates

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            await certificates.issue(db, **_certificate(patient_id, content="   "))

    with pytest.raises(BusinessRuleException, match="certifies nothing"):
        _run(_go())


# ----------------------------------------------------------------- retention
def test_the_report_counts_what_is_past_retention(session) -> None:
    """Past retention means archivable, never removable."""

    from app.services import certificates

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            await certificates.issue(
                db,
                **_certificate(
                    patient_id,
                    certificate_number="CERT-OLD",
                    issued_at=datetime.now(UTC) - timedelta(days=365 * 4),
                ),
            )
            await certificates.issue(
                db, **_certificate(patient_id, certificate_number="CERT-NEW")
            )
            await db.commit()
            return await certificates.retention_report(db)

    report = _run(_go())
    assert report["total"] == 2
    assert report["past_retention"] == 1


def test_the_report_flags_a_referral_without_a_statement(session) -> None:
    """A row written before the rule existed is exactly what this finds."""

    from sqlalchemy import select

    from app.models.medical_certificate import MedicalCertificate
    from app.services import certificates

    factory, patient_id = session

    async def _go():
        async with factory() as db:
            row = await certificates.issue(
                db,
                **_certificate(
                    patient_id,
                    certificate_type="referral",
                    case_statement="Referred for imaging.",
                ),
            )
            await db.commit()
            stored = (
                await db.execute(
                    select(MedicalCertificate).where(MedicalCertificate.id == row.id)
                )
            ).scalar_one()
            stored.case_statement = None
            await db.commit()
            return await certificates.retention_report(db)

    assert _run(_go())["referrals_without_statement"] == 1


# ----------------------------------------------------------- readiness report
def test_readiness_now_reports_four_duties(session) -> None:
    from app.services import nch_compliance

    factory, _patient_id = session

    async def _go():
        async with factory() as db:
            return await nch_compliance.readiness(db)

    body = _run(_go())
    # B52 added the institute's own statutory registrations, so the report grew a
    # fifth duty. The assertion is a subset so a new duty does not break it, but the
    # four it was written for must still be there.
    assert {
        "prescriber_registration",
        "reason_for_change",
        "certificate_register",
        "adverse_event_register",
    } <= set(body)
