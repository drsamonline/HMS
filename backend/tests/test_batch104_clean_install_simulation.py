"""Batch 104 (Milestone 6) — Clean-machine installation simulation suite.

Simulates a fresh deployment: an empty data directory, no database file,
then the exact bootstrap a packaged server runs on first launch
(``app.startup.prepare_runtime`` -> Alembic ``upgrade head``), followed by
idempotency, schema-completeness and health/version handshake checks.

These tests are the release gate for Milestone 6 "clean-machine
installation" acceptance and previously exposed release-blocking defects
in migrations 0007/0015/0018/0019 that ``create_all``-based suites could
never catch.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.db.base import Base


@pytest.fixture()
def clean_root(tmp_path: Path, monkeypatch) -> Path:
    """Point the runtime at an empty 'machine' with no database present.

    ``HHMS_APPLICATION_ROOT`` relocates every writable runtime path
    (data dir, logs, secret key, default database) into a throwaway
    directory; the module-level ``ROOT_DIR`` snapshot is patched to match
    because it is captured at import time.
    """
    root = tmp_path / "hhms-install"
    root.mkdir()
    monkeypatch.setenv("HHMS_APPLICATION_ROOT", str(root))
    monkeypatch.setenv(
        "DATABASE_URL", f"sqlite+aiosqlite:///{(root / 'data' / 'hhms.sqlite3').as_posix()}"
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
    yield root
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _db_file(root: Path) -> Path:
    return root / "data" / "hhms.sqlite3"


def test_prepare_runtime_bootstraps_empty_machine(clean_root: Path) -> None:
    """First launch on a clean machine creates dirs + full schema via Alembic."""
    from app.startup import prepare_runtime

    assert not _db_file(clean_root).exists()

    prepare_runtime()

    # Writable runtime directories exist.
    for name in ("logs", "uploads", "backups"):
        assert (clean_root / "data" / name).is_dir(), f"data/{name} missing"

    db = _db_file(clean_root)
    assert db.exists(), "database file was not created"

    with sqlite3.connect(db) as conn:
        version = conn.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

    assert version == "0029_department_service_is_active"
    # Core domain tables must all be present after a fresh upgrade chain.
    # (Table names follow the project's declared __tablename__ values.)
    for required in (
        "User",
        "Patient",
        "Visit",
        "StockBatch",
        "PrescriptionItem",
        "DispenseRecord",
        "NumberSequence",
    ):
        assert required in tables, f"missing table after clean install: {required}"


def test_prepare_runtime_is_idempotent(clean_root: Path) -> None:
    """Re-running bootstrap on an installed machine is a no-op, not a crash."""
    from app.startup import prepare_runtime

    prepare_runtime()
    with sqlite3.connect(_db_file(clean_root)) as conn:
        before = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]

    prepare_runtime()  # second launch must not error or duplicate anything

    with sqlite3.connect(_db_file(clean_root)) as conn:
        after = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]

    assert after == before
    assert version == "0029_department_service_is_active"


def test_migration_chain_head_matches_model_metadata(clean_root: Path) -> None:
    """Fresh install schema covers every table declared by the ORM models."""
    from app.startup import migration_config, run_pending_migrations

    run_pending_migrations()

    script = ScriptDirectory.from_config(migration_config())
    assert script.get_heads() == ["0029_department_service_is_active"]

    engine = create_engine(f"sqlite:///{_db_file(clean_root)}")
    with engine.connect() as conn:
        installed = set(inspect(conn).get_table_names())
    engine.dispose()

    declared = set(Base.metadata.tables.keys())
    missing = declared - installed
    assert not missing, f"migrations do not create ORM tables: {sorted(missing)}"


def test_health_and_server_identity_handshake_after_install(clean_root: Path) -> None:
    """Installed server answers health + discovery handshake consistently."""
    from app.network.discovery import server_id
    from app.startup import run_pending_migrations
    from _qa_harness import make_file_client

    run_pending_migrations()

    with make_file_client(str(_db_file(clean_root))) as (make_client, dispose):
        client = make_client()
        live = client.get("/api/v1/health/live").json()
        info = client.get("/api/v1/health/discovery").json()
        dispose()

    from app.config.settings import get_settings

    settings = get_settings()
    assert live["status"] == "healthy"
    assert live["version"] == settings.APP_VERSION
    assert live["service"] == settings.APP_NAME
    assert info["protocol"] == "hhms-lan-v1"
    assert info["server_id"] == server_id()
    assert isinstance(info["http_port"], int)


def test_fresh_login_roundtrip_on_installed_database(clean_root: Path) -> None:
    """A brand-new install can seed an operator and authenticate end-to-end."""
    from app.startup import run_pending_migrations
    from _qa_harness import make_file_client, seed_client_user, token_for_login

    run_pending_migrations()

    with make_file_client(str(_db_file(clean_root))) as (make_client, dispose):
        username, password = seed_client_user(1)
        client = make_client()
        token = token_for_login(client, username, password)
        me = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me.status_code == 200
        assert me.json()["username"] == username
        assert me.json()["is_active"] is True
        dispose()
