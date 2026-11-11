"""Gate tests for build-plan batch B10: append-only, and tamper-evident.

Two controls, tested separately because they answer different threats:

* the **trigger** stops an ordinary DELETE or UPDATE, for every client including
  raw SQL;
* the **chain** catches what the trigger cannot - an edit made after dropping the
  trigger, or a row removed at file level.

The tamper tests therefore drop the trigger first. That is not a workaround; it is
the threat model. A test that only ever exercises the trigger would prove the
easy half.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.audit_log import AuditLog
from app.services import audit
from app.services.audit_chain import head_hash, verify


# A file-backed database built by the real Alembic chain, so the migration's
# triggers exist. In-memory databases are built with ``create_all``, which does
# not run migrations - the guard would silently be missing from the very tests
# meant to prove it is there.
@pytest.fixture()
async def migrated_session(tmp_path):
    """A database built by the real Alembic chain, triggers included."""

    import app.models  # noqa: F401
    from app.config import runtime_paths as paths_module
    from app.config import settings as settings_module
    from app.db import session as session_module

    root = tmp_path / "hhms-b10"
    root.mkdir()

    from unittest import mock

    with mock.patch.object(paths_module, "application_root", lambda: root), \
         mock.patch.object(settings_module, "ROOT_DIR", root), \
         mock.patch.dict(
             "os.environ",
             {
                 "HHMS_APPLICATION_ROOT": str(root),
                 "DATABASE_URL": f"sqlite+aiosqlite:///{(root / 'data' / 'hhms.sqlite3').as_posix()}",
                 "ENVIRONMENT": "test",
             },
         ):
        settings_module.get_settings.cache_clear()
        session_module.get_engine.cache_clear()
        session_module.get_session_factory.cache_clear()

        from app.startup import prepare_runtime

        prepare_runtime()

        engine = create_async_engine(
            f"sqlite+aiosqlite:///{(root / 'data' / 'hhms.sqlite3').as_posix()}"
        )
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            yield session

        await engine.dispose()
        settings_module.get_settings.cache_clear()
        session_module.get_engine.cache_clear()
        session_module.get_session_factory.cache_clear()


async def _write(session, activity="patient.create", entity_id=1):
    await audit.record(
        session,
        actor={"sub": "1", "username": "admin", "roles": ["admin"]},
        activity=activity,
        entity_name="Patient",
        entity_id=entity_id,
        after={"first_name": "Asha"},
    )
    await session.commit()


# ------------------------------------------------------------------- triggers
async def test_delete_is_refused_by_the_database(migrated_session) -> None:
    await _write(migrated_session)

    with pytest.raises(Exception) as excinfo:
        await migrated_session.execute(text("DELETE FROM AuditLog"))
        await migrated_session.commit()

    assert "append-only" in str(excinfo.value).lower()


async def test_update_is_refused_by_the_database(migrated_session) -> None:
    await _write(migrated_session)

    with pytest.raises(Exception) as excinfo:
        await migrated_session.execute(
            text("UPDATE AuditLog SET activity = 'tampered' WHERE id = 1")
        )
        await migrated_session.commit()

    assert "append-only" in str(excinfo.value).lower()


# ---------------------------------------------------------------------- chain
async def test_a_clean_trail_verifies(migrated_session) -> None:
    for index in range(5):
        await _write(migrated_session, activity="patient.create", entity_id=index + 1)

    report = await verify(migrated_session)
    assert report.is_intact, report.first_break
    assert report.checked == 5


async def test_rows_are_linked_to_their_predecessor(migrated_session) -> None:
    for index in range(3):
        await _write(migrated_session, entity_id=index + 1)

    rows = list(
        (await migrated_session.execute(select(AuditLog).order_by(AuditLog.id)))
        .scalars()
        .all()
    )
    assert rows[0].prev_hash is None
    assert rows[1].prev_hash == rows[0].row_hash
    assert rows[2].prev_hash == rows[1].row_hash
    assert all(row.row_hash for row in rows)


async def test_editing_a_middle_row_is_reported_with_its_id(migrated_session) -> None:
    """The gate from the build plan, stated as a test."""
    for index in range(5):
        await _write(migrated_session, entity_id=index + 1)

    # Bypass the trigger the way someone with database access would.
    await migrated_session.execute(text("DROP TRIGGER trg_audit_log_no_update"))
    await migrated_session.execute(
        text("UPDATE AuditLog SET after_json = '{\"first_name\": \"Ghost\"}' WHERE id = 3")
    )
    await migrated_session.commit()

    report = await verify(migrated_session)
    assert not report.is_intact
    assert report.first_break.audit_id == 3
    assert "edited" in report.first_break.reason


async def test_removing_a_middle_row_is_reported(migrated_session) -> None:
    for index in range(5):
        await _write(migrated_session, entity_id=index + 1)

    await migrated_session.execute(text("DROP TRIGGER trg_audit_log_no_delete"))
    await migrated_session.execute(text("DELETE FROM AuditLog WHERE id = 3"))
    await migrated_session.commit()

    report = await verify(migrated_session)
    assert not report.is_intact
    # The break surfaces at the row that used to follow the removed one.
    assert report.first_break.audit_id == 4
    assert "prev_hash" in report.first_break.reason


async def test_a_row_written_outside_the_service_is_reported(migrated_session) -> None:
    await _write(migrated_session)
    await migrated_session.execute(
        text(
            "INSERT INTO AuditLog (activity, entity_name, action_timestamp) "
            "VALUES ('forged.entry', 'Patient', '2026-11-09T10:00:00+00:00')"
        )
    )
    await migrated_session.commit()

    report = await verify(migrated_session)
    assert not report.is_intact
    assert report.first_break.audit_id == 2
    assert "no hash" in report.first_break.reason


async def test_head_hash_tracks_the_newest_row(migrated_session) -> None:
    await _write(migrated_session, entity_id=1)
    first_head = await head_hash(migrated_session)
    await _write(migrated_session, entity_id=2)
    second_head = await head_hash(migrated_session)

    assert first_head and second_head
    assert first_head != second_head


async def test_verification_can_start_mid_chain(migrated_session) -> None:
    for index in range(6):
        await _write(migrated_session, entity_id=index + 1)

    report = await verify(migrated_session, start_after_id=3)
    assert report.is_intact
    assert report.checked == 3
