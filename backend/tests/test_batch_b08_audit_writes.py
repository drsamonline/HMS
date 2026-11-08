"""Gate tests for build-plan batch B08: the audit write path.

The table existed for the life of the project and no code ever wrote to it. These
tests prove the write path works, that the row lands in the caller's transaction,
and that it carries the evidence: before, after, actor, request id, address.

The transaction tests are the important ones. An audit row that survives a
rolled-back change is a lie, and a change that commits without its row is a hole.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.request_context import (
    RequestContext,
    current_request_context,
    reset_request_context,
    set_request_context,
)
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services import audit
from app.services.patient import patient_service


ADMIN = {"sub": "1", "username": "admin", "roles": ["admin"]}


@pytest.fixture()
async def db_session():
    """A fresh in-memory database per test, with the patient number sequence."""

    import app.models  # noqa: F401 - registers every mapped class
    from app.db.base import Base
    from app.models.number_sequence import NumberSequence

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(
            NumberSequence(
                sequence_name="patient_number",
                prefix="P-",
                current_value=0,
                padding_length=6,
                reset_frequency="never",
                is_active=True,
            )
        )
        await session.commit()
        yield session

    await engine.dispose()


def _new_patient(**overrides) -> PatientCreate:
    payload = {
        "first_name": "Asha",
        "last_name": "Patel",
        "gender": "female",
        "age": 30,
    }
    payload.update(overrides)
    return PatientCreate(**payload)


# ------------------------------------------------------------------ unit: diff
def test_changed_returns_only_differing_fields() -> None:
    before = {"first_name": "Asha", "city": "Vadodara", "age": 30}
    after = {"first_name": "Asha", "city": "Surat", "age": 31}
    old, new = audit.changed(before, after)
    assert old == {"city": "Vadodara", "age": 30}
    assert new == {"city": "Surat", "age": 31}
    assert "first_name" not in old


def test_changed_is_empty_when_nothing_moved() -> None:
    same = {"first_name": "Asha"}
    assert audit.changed(same, dict(same)) == ({}, {})


def test_snapshot_drops_timestamps() -> None:
    """created_at and updated_at move on every write; they are not changes."""

    patient = Patient(
        patient_number="P-000001",
        first_name="Asha",
        last_name="Patel",
        gender="female",
        age=30,
    )
    snap = audit.snapshot(patient)
    assert "first_name" in snap
    assert "created_at" not in snap
    assert "updated_at" not in snap


def test_snapshot_can_be_limited_to_named_fields() -> None:
    patient = Patient(
        patient_number="P-000001",
        first_name="Asha",
        last_name="Patel",
        gender="female",
        age=30,
    )
    snap = audit.snapshot(patient, fields={"first_name": patient.first_name})
    assert snap == {"first_name": "Asha"}


# ------------------------------------------------- unit: request context binding
def test_request_context_round_trips() -> None:
    assert current_request_context().request_id is None
    token = set_request_context(
        RequestContext(request_id="abc", ip_address="10.0.0.5", user_agent="pytest")
    )
    try:
        assert current_request_context().request_id == "abc"
    finally:
        reset_request_context(token)
    assert current_request_context().request_id is None


# ------------------------------------------------------- integration: the writes
async def test_patient_create_writes_one_row(db_session) -> None:
    patient = await patient_service.create(
        db_session, patient_in=_new_patient(), actor=ADMIN
    )

    rows = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.entity_name == "Patient")
        )
    ).scalars().all()

    assert len(rows) == 1, f"expected one audit row, found {len(rows)}"
    row = rows[0]
    assert row.activity == "patient.create"
    assert row.entity_id == patient.id
    assert row.outcome == "success"
    assert row.user_id == 1
    assert row.actor_username == "admin"
    assert row.actor_role == "admin"
    assert row.before_json is None, "a create has no before"
    assert json.loads(row.after_json)["first_name"] == "Asha"


async def test_patient_update_records_the_changed_field_both_ways(db_session) -> None:
    """The gate from the build plan, stated as a test."""
    patient = await patient_service.create(
        db_session, patient_in=_new_patient(), actor=ADMIN
    )

    await patient_service.update(
        db_session,
        patient_id=patient.id,
        patient_in=PatientUpdate(city="Surat"),
        actor=ADMIN,
        reason="patient moved",
    )

    row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.activity == "patient.update")
        )
    ).scalars().one()

    assert json.loads(row.before_json) == {"city": None}
    assert json.loads(row.after_json) == {"city": "Surat"}
    assert row.reason == "patient moved"
    assert row.entity_id == patient.id


async def test_patient_update_that_changes_nothing_writes_no_row(db_session) -> None:
    patient = await patient_service.create(
        db_session, patient_in=_new_patient(), actor=ADMIN
    )
    await patient_service.update(
        db_session,
        patient_id=patient.id,
        patient_in=PatientUpdate(city="Surat"),
        actor=ADMIN,
    )
    # The same value again: the service must not record a change that did not
    # happen, or the trail fills with noise and stops being evidence.
    await patient_service.update(
        db_session,
        patient_id=patient.id,
        patient_in=PatientUpdate(city="Surat"),
        actor=ADMIN,
    )

    rows = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.activity == "patient.update")
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_deactivate_records_the_flag_transition(db_session) -> None:
    patient = await patient_service.create(
        db_session, patient_in=_new_patient(), actor=ADMIN
    )
    await patient_service.deactivate(db_session, patient_id=patient.id, actor=ADMIN)

    row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.activity == "patient.deactivate")
        )
    ).scalars().one()
    assert json.loads(row.before_json) == {"is_active": True}
    assert json.loads(row.after_json) == {"is_active": False}


async def test_request_context_lands_on_the_row(db_session) -> None:
    token = set_request_context(
        RequestContext(
            request_id="11111111-1111-1111-1111-111111111111",
            ip_address="10.1.2.3",
            user_agent="HHMS-Client/0.0.2",
        )
    )
    try:
        await patient_service.create(
            db_session, patient_in=_new_patient(), actor=ADMIN
        )
    finally:
        reset_request_context(token)

    row = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.activity == "patient.create")
        )
    ).scalars().one()
    assert row.request_id == "11111111-1111-1111-1111-111111111111"
    assert row.ip_address == "10.1.2.3"
    assert row.user_agent == "HHMS-Client/0.0.2"


async def test_a_system_action_records_without_an_actor(db_session) -> None:
    """Not every write has a person behind it; the row is still valid."""
    await patient_service.create(db_session, patient_in=_new_patient(), actor=None)
    row = (await db_session.execute(select(AuditLog))).scalars().one()
    assert row.user_id is None
    assert row.actor_username is None


async def test_audit_row_rolls_back_with_the_change(db_session) -> None:
    """The row must not outlive a failed business operation."""
    with pytest.raises(RuntimeError):
        await audit.record(
            db_session,
            actor=ADMIN,
            activity="patient.create",
            entity_name="Patient",
            entity_id=1,
            after={"first_name": "Ghost"},
        )
        raise RuntimeError("the business operation failed after recording")
    await db_session.rollback()

    rows = (await db_session.execute(select(AuditLog))).scalars().all()
    assert rows == [], "an audit row survived a rolled-back transaction"


# ------------------------------------- end to end: the middleware really binds
def test_http_request_records_request_id_and_address() -> None:
    """Prove the contextvar survives the real middleware stack.

    The unit test above sets the context by hand, which proves the service can
    read it - not that the middleware writes it. Middleware runs in a different
    task from the endpoint in some Starlette versions, and a context that does
    not propagate fails silently: every audit row simply has a null request id.
    """

    import asyncio

    from sqlalchemy import select

    from app.models.audit_log import AuditLog
    from tests._qa_harness import (
        make_client,
        seed_number_sequence,
        seed_user,
        token_for_login,
    )

    with make_client() as client:
        user_id = seed_user(username="qa-b08", password="qa-b08-password")
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        token = token_for_login(client, "qa-b08", "qa-b08-password")

        response = client.post(
            "/api/v1/patients",
            json={
                "first_name": "Asha",
                "last_name": "Patel",
                "gender": "female",
                "age": 30,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "HHMS-Client/b08",
            },
        )
        assert response.status_code == 201, response.text
        request_id = response.headers.get("X-Request-ID")

        from app.db.session import get_session_factory

        factory = get_session_factory()

        async def _read():
            async with factory() as db:
                rows = (await db.execute(select(AuditLog))).scalars().all()
                return [
                    (r.activity, r.request_id, r.ip_address, r.user_agent, r.user_id)
                    for r in rows
                ]

        rows = asyncio.run(_read())

    assert len(rows) == 1, f"expected one audit row, found {rows}"
    activity, recorded_request_id, ip_address, user_agent, actor = rows[0]
    assert activity == "patient.create"
    assert recorded_request_id == request_id, (
        "the audit row's request id must match the one the client was given; a "
        "mismatch means the context did not propagate through the middleware"
    )
    assert recorded_request_id is not None
    assert ip_address is not None, "the client address did not reach the service"
    assert user_agent == "HHMS-Client/b08"
    assert actor == user_id
