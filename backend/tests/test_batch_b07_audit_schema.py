"""Gate tests for build-plan batch B07: the audit schema.

An audit row is only evidence if it can say who acted, what they did, what the
record said before and after, and why. These tests prove that the ORM model, the
Alembic migration and a freshly bootstrapped database all agree on that shape.

The suite's other databases are built from ``Base.metadata.create_all``, so they
would pass even if the migration were wrong. That is exactly the failure mode
migration 0029 was written to fix, which is why one test here runs the real
Alembic chain against a throwaway database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.models.audit_log import AuditLog

REQUIRED_COLUMNS = {
    "id",
    "user_id",
    "actor_username",
    "actor_role",
    "activity",
    "outcome",
    "entity_name",
    "entity_id",
    "before_json",
    "after_json",
    "reason",
    "action_timestamp",
    "request_id",
    "ip_address",
    "user_agent",
    "remarks",
}

# Columns the earlier plan named but that would duplicate an existing one.
FORBIDDEN_DUPLICATES = {"actor_id", "action", "occurred_at"}


@pytest.fixture()
def bootstrapped_db(tmp_path: Path, monkeypatch) -> Path:
    """Run the real Alembic chain against a throwaway database."""
    root = tmp_path / "hhms-b07"
    root.mkdir()
    monkeypatch.setenv("HHMS_APPLICATION_ROOT", str(root))
    # Pin the database explicitly. Relying on the root alone leaves the URL to
    # whatever a previous test module left cached, and the failure mode is a
    # silently empty file rather than an error.
    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{(root / 'data' / 'hhms.sqlite3').as_posix()}",
    )
    monkeypatch.setenv("ENVIRONMENT", "test")

    from app.config import runtime_paths as paths_module
    from app.config import settings as settings_module
    from app.db import session as session_module

    monkeypatch.setattr(paths_module, "application_root", lambda: root)
    monkeypatch.setattr(settings_module, "ROOT_DIR", root)
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    from app.startup import prepare_runtime

    prepare_runtime()
    database = root / "data" / "hhms.sqlite3"
    assert database.is_file(), (
        "prepare_runtime() did not create the database at the configured URL; "
        "the fixture is measuring the wrong file"
    )
    yield database

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


# ------------------------------------------------------------------ the model
def test_model_declares_every_required_column() -> None:
    declared = set(AuditLog.__table__.columns.keys())
    missing = REQUIRED_COLUMNS - declared
    assert not missing, f"AuditLog is missing {sorted(missing)}"


def test_model_does_not_carry_duplicate_concepts() -> None:
    declared = set(AuditLog.__table__.columns.keys())
    duplicates = FORBIDDEN_DUPLICATES & declared
    assert not duplicates, (
        f"{sorted(duplicates)} duplicate a column that already exists "
        "(user_id, activity, action_timestamp). Two columns meaning one thing "
        "become two sources of truth."
    )


def test_actor_is_nullable_but_activity_is_not() -> None:
    """A failed login for an unknown username must be recordable."""
    assert AuditLog.__table__.columns["user_id"].nullable is True
    assert AuditLog.__table__.columns["activity"].nullable is False
    assert AuditLog.__table__.columns["entity_name"].nullable is False
    assert AuditLog.__table__.columns["action_timestamp"].nullable is False


def test_evidence_columns_are_optional() -> None:
    """A read-only action has no before or after; the row is still valid."""
    for name in ("before_json", "after_json", "reason", "request_id"):
        assert AuditLog.__table__.columns[name].nullable is True


# -------------------------------------------------------------- the migration
def test_migration_creates_the_columns(bootstrapped_db: Path) -> None:
    with sqlite3.connect(bootstrapped_db) as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(AuditLog)")
        }
        version = conn.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]

    missing = REQUIRED_COLUMNS - columns
    assert not missing, f"migration did not create {sorted(missing)}"
    assert version == "0031_audit_log_hash_chain"


def test_migration_and_model_agree(bootstrapped_db: Path) -> None:
    """The drift this catches is the one migration 0029 was written to repair."""
    with sqlite3.connect(bootstrapped_db) as conn:
        migrated = {row[1] for row in conn.execute("PRAGMA table_info(AuditLog)")}
    declared = set(AuditLog.__table__.columns.keys())
    assert migrated == declared, (
        f"only in migration: {sorted(migrated - declared)}; "
        f"only in model: {sorted(declared - migrated)}"
    )


def test_indexes_for_the_two_questions(bootstrapped_db: Path) -> None:
    with sqlite3.connect(bootstrapped_db) as conn:
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(AuditLog)")}
    assert "ix_audit_log_entity" in indexes
    assert "ix_audit_log_actor_time" in indexes
    assert "ix_audit_log_request_id" in indexes


def test_outcome_defaults_to_success(bootstrapped_db: Path) -> None:
    with sqlite3.connect(bootstrapped_db) as conn:
        conn.execute(
            "INSERT INTO AuditLog "
            "(activity, entity_name, action_timestamp) "
            "VALUES ('patient.create', 'Patient', '2026-11-09T10:00:00+00:00')"
        )
        outcome = conn.execute("SELECT outcome FROM AuditLog").fetchone()[0]
    assert outcome == "success"


def test_a_row_without_an_actor_is_accepted(bootstrapped_db: Path) -> None:
    """The case that motivates the nullable user_id: an unknown username."""
    with sqlite3.connect(bootstrapped_db) as conn:
        conn.execute(
            "INSERT INTO AuditLog "
            "(activity, entity_name, action_timestamp, outcome, actor_username) "
            "VALUES ('auth.login', 'User', '2026-11-09T10:00:00+00:00', "
            "'failure', 'unknown-user')"
        )
        row = conn.execute(
            "SELECT actor_username, outcome FROM AuditLog"
        ).fetchone()
    assert row == ("unknown-user", "failure")
