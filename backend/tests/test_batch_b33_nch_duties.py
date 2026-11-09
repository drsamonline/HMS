"""Gate tests for build-plan batch B33: the NCH duties that software can enforce.

Two of the National Commission for Homoeopathy's Code of Ethics Regulations 2022
make a record incomplete when a field is missing, so they are enforced where the
record is written. The third is a readiness report rather than a block, because a
hospital that has just installed the software has no registration numbers yet, and
refusing every prescription until they are typed in would make the product unusable
on day one.

Tested at the service level: the rule and the report are the subject, and driving
them through the HTTP layer would test the route plumbing instead.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.models.case_record import CaseRecord
from app.models.followup import FollowUp
from app.models.patient import Patient
from app.models.user import User


@pytest.fixture()
def session(tmp_path, monkeypatch):
    """A database with one patient, one case record and one clinician."""

    from app.config import settings as settings_module
    from app.db import session as session_module
    from app.db.base import Base

    path = tmp_path / "hhms-b33.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{path.as_posix()}")
    monkeypatch.setenv("ENVIRONMENT", "test")
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")

    async def _seed() -> dict:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
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
            await db.flush()
            # case_family_id is NOT NULL and minted by the service; a hand-built
            # row would have to invent it, so the real creation path is used.
            case = CaseRecord(
                patient_id=patient.id,
                case_number="C-0001",
                case_family_id="F-0001",
                case_year=now.year,
                storage_tier="live",
                is_current_year=True,
                case_status="draft",
                created_by=1,
                created_at=now,
                updated_at=now,
            )
            db.add(case)
            await db.flush()
            ids = {"patient_id": patient.id, "case_record_id": case.id}
            await db.commit()
        return factory, ids

    loop = asyncio.new_event_loop()
    try:
        factory, ids = loop.run_until_complete(_seed())
    finally:
        loop.close()

    yield factory, ids

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ------------------------------------------------------- reason for change
def _followup_payload(ids: dict, **overrides):
    from app.schemas.followup import FollowUpCreate

    base = {
        "case_record_id": ids["case_record_id"],
        "patient_id": ids["patient_id"],
        "followup_datetime": datetime.now(UTC),
        "decision": "repeat",
    }
    base.update(overrides)
    return FollowUpCreate(**base)


def test_a_change_of_treatment_needs_a_reason(session) -> None:
    """NCH Code of Ethics 31(1), enforced where the reason is still known."""

    from app.core.exceptions import BusinessRuleException
    from app.services.followup import followup_service

    factory, ids = session

    async def _go():
        async with factory() as db:
            return await followup_service.create(
                db, _followup_payload(ids, decision="change_remedy"), recorded_by=1
            )

    with pytest.raises(BusinessRuleException, match="needs a reason"):
        _run(_go())


def test_a_continuation_needs_no_reason(session) -> None:
    """Only a change needs one; continuing the same treatment is not a change."""

    from app.services.followup import followup_service

    factory, ids = session

    async def _go():
        async with factory() as db:
            return await followup_service.create(
                db, _followup_payload(ids, decision="repeat"), recorded_by=1
            )

    assert _run(_go()) is not None


def test_a_change_with_a_reason_is_stored(session) -> None:
    from app.services.followup import followup_service

    factory, ids = session

    async def _go():
        async with factory() as db:
            row = await followup_service.create(
                db,
                _followup_payload(
                    ids,
                    decision="change_remedy",
                    reason_for_change="No response after four weeks; worse at night.",
                ),
                recorded_by=1,
            )
            return row.reason_for_change

    assert _run(_go()).startswith("No response")


# ---------------------------------------------------------- readiness report
def test_readiness_reports_all_three_duties(session) -> None:
    from app.services import nch_compliance

    factory, _ids = session

    async def _go():
        async with factory() as db:
            return await nch_compliance.readiness(db)

    body = _run(_go())
    assert set(body) == {
        "prescriber_registration",
        "reason_for_change",
        "adverse_event_register",
    }


def test_readiness_names_a_practitioner_without_a_registration_number(session) -> None:
    """NCH Code of Ethics 7(2)."""

    from app.models.role import Role
    from app.models.user_role import UserRole
    from app.services import nch_compliance

    factory, _ids = session

    async def _go():
        async with factory() as db:
            role = Role(role_name="medical officer", description="doctor")
            user = User(
                username="dr.rao",
                password_hash="x",
                full_name="Dr Rao",
                is_active=True,
            )
            db.add_all([role, user])
            await db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.commit()
            return await nch_compliance.readiness(db)

    body = _run(_go())
    entry = body["prescriber_registration"]
    assert entry["ok"] is False
    assert entry["missing_count"] == 1
    assert entry["practitioners"][0]["username"] == "dr.rao"


def test_a_practitioner_with_a_number_is_not_reported(session) -> None:
    from app.models.role import Role
    from app.models.user_role import UserRole
    from app.services import nch_compliance

    factory, _ids = session

    async def _go():
        async with factory() as db:
            role = Role(role_name="medical officer", description="doctor")
            user = User(
                username="dr.rao",
                password_hash="x",
                full_name="Dr Rao",
                is_active=True,
                registration_number="NCH/2021/0042",
            )
            db.add_all([role, user])
            await db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.commit()
            return await nch_compliance.readiness(db)

    assert _run(_go())["prescriber_registration"]["ok"] is True


def test_readiness_counts_followups_that_changed_without_a_reason(session) -> None:
    """Rows written before the rule existed are exactly what this finds."""

    from app.services import nch_compliance

    factory, ids = session

    async def _go():
        async with factory() as db:
            db.add(
                FollowUp(
                    case_record_id=ids["case_record_id"],
                    patient_id=ids["patient_id"],
                    followup_datetime=datetime.now(UTC),
                    decision="change_remedy",
                    reason_for_change=None,
                    recorded_by=1,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )
            await db.commit()
            return await nch_compliance.readiness(db)

    entry = _run(_go())["reason_for_change"]
    assert entry["missing_count"] == 1
    assert entry["ok"] is False


def test_readiness_reports_the_unimplemented_duty_honestly(session) -> None:
    """Pharmacovigilance is its own batch; the report says so rather than passing."""

    from app.services import nch_compliance

    factory, _ids = session

    async def _go():
        async with factory() as db:
            return await nch_compliance.readiness(db)

    adverse = _run(_go())["adverse_event_register"]
    assert adverse["ok"] is False
    assert "Not implemented yet" in adverse["note"]


# --------------------------------------------------------------------- fields
def test_the_registration_number_belongs_to_the_practitioner() -> None:
    """A document inherits it; the person owns it."""

    assert "registration_number" in User.__table__.columns
    assert "reason_for_change" in FollowUp.__table__.columns
