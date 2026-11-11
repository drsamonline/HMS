"""Gate tests for build-plan batch B16: the module registry.

Two halves. The registry is capability - what a module is, what it depends on -
and is tested in isolation. `ModuleState` is this hospital's choice, and is tested
against a real Alembic chain, because the migration derives it from existing data
and a derivation that is wrong would switch a working hospital's pharmacy off.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.core.permissions import CODES
from app.modules.registry import BY_CODE, MODULES, dependents, depends_on, resolve


# ------------------------------------------------------------- the capability
def test_core_is_the_only_immovable_module() -> None:
    core = [module.code for module in MODULES if module.is_core]
    assert core == ["core"]


def test_every_module_declares_permissions_that_exist() -> None:
    for module in MODULES:
        unknown = [code for code in module.permissions if code not in CODES]
        assert not unknown, f"{module.code} declares undeclared codes: {unknown}"


def test_every_module_has_a_name_and_a_summary() -> None:
    for module in MODULES:
        assert module.name.strip(), module.code
        assert module.summary.strip(), module.code


def test_dependencies_are_declared_and_acyclic() -> None:
    for module in MODULES:
        for dependency in module.depends_on:
            assert dependency in BY_CODE, f"{module.code} depends on unknown {dependency}"
            assert dependency != module.code
            assert module.code not in depends_on(dependency), (
                f"cycle: {module.code} -> {dependency} -> {module.code}"
            )


def test_enabling_a_module_brings_its_prerequisites() -> None:
    assert resolve("pharmacy", set()) == {"core", "pharmacy"}
    assert resolve("nabh", set()) == {"core", "nabh"}


def test_resolving_never_removes_an_enabled_module() -> None:
    """Enabling one thing must not switch another off as a side effect."""

    assert resolve("billing", {"ipd", "laboratory"}) == {
        "core", "billing", "ipd", "laboratory"
    }


def test_core_reports_every_module_as_a_dependent() -> None:
    assert set(dependents("core")) == {
        module.code for module in MODULES if module.code != "core"
    }


def test_a_leaf_module_has_no_dependents() -> None:
    assert dependents("stock") == ()
    assert dependents("billing") == ()


# ------------------------------------------------------------- the state table
@pytest.fixture()
def migrated(tmp_path, monkeypatch):
    """A database built by the real Alembic chain, with a dispense row in it."""

    root = tmp_path / "hhms-b16"
    root.mkdir()
    monkeypatch.setenv("HHMS_APPLICATION_ROOT", str(root))
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

    yield root

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _bootstrap(root: Path) -> Path:
    from app.startup import prepare_runtime

    prepare_runtime()
    database = root / "data" / "hhms.sqlite3"
    assert database.is_file()
    return database


def test_a_fresh_install_enables_only_core(migrated) -> None:
    database = _bootstrap(migrated)

    with sqlite3.connect(database) as conn:
        rows = dict(
            conn.execute("SELECT module_code, is_enabled FROM ModuleState").fetchall()
        )

    assert rows["core"] == 1
    for code, enabled in rows.items():
        if code != "core":
            assert enabled == 0, f"{code} should be off on a fresh install"


def test_the_migration_derives_state_from_existing_records(migrated) -> None:
    """The gate from the build plan: dispense rows mean pharmacy was in use."""

    database = _bootstrap(migrated)

    # A hospital that has been dispensing, and doing nothing else.
    with sqlite3.connect(database) as conn:
        conn.execute(
            "INSERT INTO DispenseRecord "
            "(medicine_id, stock_batch_id, quantity_dispensed, dispensed_by) "
            "VALUES (1, 1, 1, 1)"
        )
        conn.commit()

    # Re-run the derivation by stepping back one revision and forward again.
    from alembic import command

    from app.startup import migration_config

    config = migration_config()
    command.downgrade(config, "0033_all_access_roles")
    command.upgrade(config, "head")

    with sqlite3.connect(database) as conn:
        rows = dict(
            conn.execute("SELECT module_code, is_enabled FROM ModuleState").fetchall()
        )

    assert rows["pharmacy"] == 1, "a dispense row must enable pharmacy"
    assert rows["core"] == 1
    for code in ("ipd", "laboratory", "billing", "mrd", "stock", "nabh"):
        assert rows[code] == 0, f"{code} has no records and must stay off"


def test_module_state_has_one_row_per_module(migrated) -> None:
    database = _bootstrap(migrated)
    with sqlite3.connect(database) as conn:
        codes = [row[0] for row in conn.execute("SELECT module_code FROM ModuleState")]
    assert sorted(codes) == sorted(BY_CODE), "one row per declared module"
