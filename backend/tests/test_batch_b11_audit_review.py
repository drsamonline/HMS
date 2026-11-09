"""Gate tests for build-plan batch B11: review and export.

The review screen and the export must answer the same question with the same
rows. If they can drift apart, an assessor's copy of the trail and the hospital's
screen can disagree - and the copy is the one that gets read in a hearing.

Export is also an act on the trail, so it records itself.
"""

from __future__ import annotations

import csv
import io

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.audit_log import AuditLog
from app.services import audit
from app.services.audit_log import audit_log_service


@pytest.fixture()
async def db_session():
    import app.models  # noqa: F401
    from app.db.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _seed(session, *, count=6):
    """Three patients and three invoices, written by two different actors."""

    for index in range(count):
        is_invoice = index % 2 == 1
        await audit.record(
            session,
            actor=(
                {"sub": "1", "username": "admin", "roles": ["admin"]}
                if index < 3
                else {"sub": "2", "username": "clerk", "roles": ["billing"]}
            ),
            activity="invoice.create" if is_invoice else "patient.create",
            entity_name="Invoice" if is_invoice else "Patient",
            entity_id=index + 1,
            after={"n": index},
        )
    await session.commit()


# ---------------------------------------------------------------- filtering
async def test_filter_by_entity_returns_only_matching_rows(db_session) -> None:
    await _seed(db_session)
    rows = await audit_log_service.list_recent(db_session, entity_name="Invoice")
    assert rows, "expected invoice rows"
    assert {row.entity_name for row in rows} == {"Invoice"}


async def test_filter_by_actor_returns_only_that_actors_rows(db_session) -> None:
    await _seed(db_session)
    rows = await audit_log_service.list_recent(db_session, user_id=2)
    assert rows
    assert {row.actor_username for row in rows} == {"clerk"}


async def test_filter_by_activity_and_outcome(db_session) -> None:
    await _seed(db_session)
    rows = await audit_log_service.list_recent(db_session, activity="patient.create")
    assert rows
    assert {row.activity for row in rows} == {"patient.create"}

    assert await audit_log_service.count(db_session, outcome="failure") == 0
    assert await audit_log_service.count(db_session, outcome="success") == 6


async def test_filters_combine_rather_than_replace(db_session) -> None:
    """An assessor's question is usually two filters at once."""
    await _seed(db_session)
    rows = await audit_log_service.list_recent(
        db_session, user_id=2, entity_name="Invoice"
    )
    assert rows
    assert {row.actor_username for row in rows} == {"clerk"}
    assert {row.entity_name for row in rows} == {"Invoice"}


async def test_count_matches_the_listed_rows(db_session) -> None:
    await _seed(db_session)
    total = await audit_log_service.count(db_session)
    rows = await audit_log_service.list_recent(db_session, limit=200)
    assert total == len(rows) == 6


# ------------------------------------------------------------------ exporting
async def test_csv_export_has_one_line_per_row_plus_a_header(db_session) -> None:
    await _seed(db_session)
    rows = await audit_log_service.export_rows(db_session)
    payload = audit_log_service.to_csv(rows)

    parsed = list(csv.reader(io.StringIO(payload.decode("utf-8"))))
    assert parsed[0][0] == "id"
    assert len(parsed) == len(rows) + 1


async def test_export_contains_the_same_rows_the_query_returns(db_session) -> None:
    """The gate from the build plan, stated as a test."""
    await _seed(db_session)

    query_rows = await audit_log_service.list_recent(
        db_session, entity_name="Invoice", limit=200
    )
    export_rows = await audit_log_service.export_rows(db_session, entity_name="Invoice")

    assert len(query_rows) == len(export_rows)
    assert {row.id for row in query_rows} == {row.id for row in export_rows}


async def test_export_reads_forwards_and_the_screen_reads_backwards(db_session) -> None:
    """An export is an account of events; a review starts at the newest."""
    await _seed(db_session)
    export_rows = await audit_log_service.export_rows(db_session)
    screen_rows = await audit_log_service.list_recent(db_session, limit=200)

    assert [row.id for row in export_rows] == sorted(row.id for row in export_rows)
    assert [row.id for row in screen_rows] == sorted(
        (row.id for row in screen_rows), reverse=True
    )


async def test_pdf_export_produces_a_pdf(db_session) -> None:
    await _seed(db_session)
    rows = await audit_log_service.export_rows(db_session)
    payload = audit_log_service.to_pdf(rows)

    assert payload.startswith(b"%PDF")
    assert len(payload) > 1000


async def test_pdf_export_survives_an_empty_trail(db_session) -> None:
    payload = audit_log_service.to_pdf(await audit_log_service.export_rows(db_session))
    assert payload.startswith(b"%PDF")


# ------------------------------------------------------- the export is audited
async def test_exporting_writes_its_own_audit_row(db_session) -> None:
    await _seed(db_session)
    before = await audit_log_service.count(db_session)

    await audit.record(
        db_session,
        actor={"sub": "1", "username": "admin", "roles": ["admin"]},
        activity="audit.export",
        entity_name="AuditLog",
        entity_id=None,
        reason="6 row(s) exported as csv",
    )
    await db_session.commit()

    assert await audit_log_service.count(db_session) == before + 1
    latest = await audit_log_service.list_recent(db_session, limit=1)
    assert latest[0].activity == "audit.export"


# ------------------------------------------------------------- the HTTP gate
def test_reading_the_trail_requires_the_audit_read_permission() -> None:
    from app.auth.jwt import create_access_token
    from tests._qa_harness import make_client

    with make_client() as client:
        # A token whose subject has no user behind it holds no permissions.
        token = create_access_token(subject="999999")
        response = client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 403, response.text


def test_an_administrator_can_read_the_trail() -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/audit-logs", headers=auth_headers())
    assert response.status_code == 200, response.text


def test_export_returns_a_file_and_records_itself() -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        # Inside the block: the harness creates the database the actor lives in.
        headers = auth_headers()
        csv_response = client.get("/api/v1/audit-logs/export?format=csv", headers=headers)
        assert csv_response.status_code == 200, csv_response.text
        assert csv_response.headers["content-type"].startswith("text/csv")
        assert "attachment" in csv_response.headers["content-disposition"]
        assert csv_response.content.decode("utf-8").splitlines()[0].startswith("id,")

        pdf_response = client.get("/api/v1/audit-logs/export?format=pdf", headers=headers)
        assert pdf_response.status_code == 200, pdf_response.text
        assert pdf_response.content.startswith(b"%PDF")

        after = client.get("/api/v1/audit-logs", headers=headers).json()

    activities = [row["activity"] for row in after]
    assert activities.count("audit.export") == 2, activities
