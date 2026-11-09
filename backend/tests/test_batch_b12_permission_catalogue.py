"""Gate tests for build-plan batch B12: the permission catalogue.

A catalogue that disagrees with itself, or with the database, is worse than none:
an administrator grants a code, the route checks a different one, and the screen
is empty for a reason nobody can find. So the gate checks three things - the
catalogue is internally sound, the migration seeds exactly it, and it covers the
modules the application actually has.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

from app.core.permissions import (
    ALL,
    BY_CODE,
    CODES,
    PERMISSIONS,
    ROLE_TEMPLATES,
    expand,
    unknown_codes,
)

ENDPOINTS = Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "endpoints"
MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "0032_permission_catalogue.py"
)

#: Endpoint modules that carry no hospital data and therefore need no permission:
#: the health probe, the login route, and the module that serves the GUI itself.
#: ``navigation`` returns the caller's own menu, so it needs a login and no
#: particular permission - see AUTHENTICATED_ONLY_PATHS. ``setup`` runs before any
#: user exists and carries the setup code instead of a permission.
NO_PERMISSION_NEEDED = {"__init__", "auth", "health", "navigation"}


def _load_migration():
    spec = importlib.util.spec_from_file_location("perm_migration", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------ internal soundness
def test_codes_are_unique() -> None:
    codes = [spec.code for spec in PERMISSIONS]
    assert len(codes) == len(set(codes)), "duplicate permission code in the catalogue"


def test_names_are_unique() -> None:
    """Permission.name is UNIQUE in the schema; a clash fails the migration."""
    names = [spec.name for spec in PERMISSIONS]
    duplicates = {name for name in names if names.count(name) > 1}
    assert not duplicates, f"duplicate permission names: {sorted(duplicates)}"


def test_codes_are_module_dot_verb() -> None:
    for spec in PERMISSIONS:
        assert re.fullmatch(r"[a-z]+(\.[a-z]+)+", spec.code), spec.code
        assert spec.code.split(".")[0] == spec.module, (
            f"{spec.code} is filed under module {spec.module}"
        )


def test_every_spec_has_a_description() -> None:
    for spec in PERMISSIONS:
        assert spec.description.strip(), f"{spec.code} has no description"
        assert spec.name.strip(), f"{spec.code} has no name"


# --------------------------------------------------------------- role templates
def test_role_templates_only_use_declared_codes() -> None:
    for role, template in ROLE_TEMPLATES.items():
        missing = unknown_codes(template)
        assert not missing, f"role {role} grants undeclared codes: {sorted(missing)}"


def test_administrator_holds_everything() -> None:
    assert expand(ROLE_TEMPLATES["administrator"]) == CODES


def test_the_auditor_cannot_change_anything() -> None:
    """The role exists so that reading can be granted without writing."""
    granted = expand(ROLE_TEMPLATES["auditor"])
    writes = {code for code in granted if code.endswith((".write", ".void", ".deactivate"))}
    assert not writes, f"auditor holds write permissions: {sorted(writes)}"


# --------------------------------------------------------- catalogue vs migration
def test_migration_seeds_exactly_the_catalogue() -> None:
    """The duplicate is deliberate; drift between them must fail the build."""
    migration = _load_migration()
    seeded = {(row[0], row[1]) for row in migration.PERMISSIONS}
    declared = {(spec.code, spec.module) for spec in PERMISSIONS}
    assert seeded == declared, (
        f"only in migration: {sorted(seeded - declared)}; "
        f"only in catalogue: {sorted(declared - seeded)}"
    )


def test_migration_role_templates_match_the_catalogue() -> None:
    migration = _load_migration()
    assert migration.ROLE_TEMPLATES == ROLE_TEMPLATES


# ----------------------------------------------------------------- completeness
def test_every_data_endpoint_module_is_covered() -> None:
    """A module with routes but no permission is a module nobody can protect."""

    modules = {path.stem for path in ENDPOINTS.glob("*.py")} - NO_PERMISSION_NEEDED
    covered = {spec.module for spec in PERMISSIONS}

    # One endpoint file can serve several catalogue modules (administration
    # serves users, roles, settings and masters), so the mapping is a set. It is
    # explicit so that a new endpoint file is a decision rather than an oversight.
    mapping: dict[str, set[str]] = {
        "administration": {"users", "roles", "settings", "masters"},
        "admissions": {"ipd"},
        "archive_records": {"mrd"},
        "audit_logs": {"audit"},
        "backups": {"backup"},
        "beds": {"ipd"},
        "billing": {"billing"},
        "case_records": {"clinical"},
        "compliance": {"audit"},
        "configuration": {"settings"},
        "dashboard": {"reporting"},
        "department_services": {"masters"},
        "departments": {"masters"},
        "designations": {"masters"},
        "diagnoses": {"clinical"},
        "diet_charts": {"clinical"},
        "discharges": {"ipd"},
        "dispenses": {"pharmacy"},
        "followups": {"clinical"},
        "goods_receipts": {"procurement"},
        "icd11": {"masters"},
        "inventory_items": {"inventory"},
        "investigation_results": {"investigations"},
        "investigations": {"investigations"},
        "ipd_assessments": {"ipd"},
        "maintenance": {"maintenance"},
        "medical_documents": {"mrd"},
        "medicine_batches": {"pharmacy"},
        "medicines": {"pharmacy"},
        "nutritional_assessments": {"clinical"},
        "opd_tokens": {"opd"},
        "operational_year": {"maintenance", "health"},
        "pain_assessments": {"clinical"},
        "patient_files": {"mrd"},
        "patient_history": {"patients"},
        "patients": {"patients"},
        "prescriptions": {"prescriptions"},
        "procurement": {"procurement"},
        "progress_notes": {"clinical"},
        "report_pdf": {"reporting"},
        "reporting": {"reporting"},
        "service_activities": {"masters"},
        "settings": {"settings"},
        "setup": set(),
        "statistics": {"reporting"},
        "stock_batches": {"inventory"},
        "stock_cards": {"inventory"},
        "stock_transactions": {"inventory"},
        "visits": {"opd"},
    }

    unmapped = modules - set(mapping)
    assert not unmapped, (
        f"{sorted(unmapped)} have routes but no entry in the module mapping. Add "
        "one and make sure the catalogue covers the target modules."
    )

    mapped_modules = set().union(*mapping.values())
    unknown_targets = mapped_modules - covered
    assert not unknown_targets, (
        f"{sorted(unknown_targets)} are mapped to but have no permission declared"
    )


def test_no_permission_is_declared_that_no_endpoint_needs() -> None:
    """A code nothing can check is a code an administrator grants for nothing."""
    used = {
        "patients", "opd", "clinical", "prescriptions", "ipd", "investigations",
        "pharmacy", "inventory", "procurement", "billing", "mrd", "reporting",
        "audit", "users", "roles", "settings", "masters", "backup",
        "maintenance", "health",
    }
    orphans = {spec.module for spec in PERMISSIONS} - used
    assert not orphans, f"catalogue declares modules no endpoint maps to: {sorted(orphans)}"


def test_wildcard_expands_to_every_code() -> None:
    assert ALL == "*"
    assert BY_CODE.keys() == CODES


# ------------------------------------------------------------ against a database
@pytest.fixture()
def bootstrapped_db(tmp_path, monkeypatch):
    """Run the real Alembic chain so the seeding statements are exercised."""

    root = tmp_path / "hhms-b12"
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

    from app.startup import prepare_runtime

    prepare_runtime()
    database = root / "data" / "hhms.sqlite3"
    assert database.is_file()
    yield database

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def test_database_holds_exactly_the_catalogue(bootstrapped_db) -> None:
    import sqlite3

    with sqlite3.connect(bootstrapped_db) as conn:
        rows = {row[0] for row in conn.execute("SELECT code FROM Permission")}
    assert rows == set(CODES), (
        f"only in db: {sorted(rows - set(CODES))}; "
        f"only in catalogue: {sorted(set(CODES) - rows)}"
    )


def test_database_holds_the_role_templates(bootstrapped_db) -> None:
    import sqlite3

    with sqlite3.connect(bootstrapped_db) as conn:
        roles = {row[0] for row in conn.execute("SELECT role_name FROM Role")}
    assert set(ROLE_TEMPLATES).issubset(roles), (
        f"roles missing after migration: {sorted(set(ROLE_TEMPLATES) - roles)}"
    )


def test_every_template_grant_landed(bootstrapped_db) -> None:
    import sqlite3

    with sqlite3.connect(bootstrapped_db) as conn:
        grants: dict[str, set[str]] = {}
        for role_name, code in conn.execute(
            "SELECT r.role_name, p.code FROM RolePermission rp "
            "JOIN Role r ON r.id = rp.role_id "
            "JOIN Permission p ON p.id = rp.permission_id"
        ):
            grants.setdefault(role_name, set()).add(code)

    for role, template in ROLE_TEMPLATES.items():
        expected = set(expand(template))
        assert grants.get(role, set()) == expected, (
            f"{role}: missing {sorted(expected - grants.get(role, set()))}, "
            f"unexpected {sorted(grants.get(role, set()) - expected)}"
        )


def test_migration_is_idempotent(bootstrapped_db) -> None:
    """Re-running the seed must not duplicate grants or fail on uniqueness."""
    import sqlite3

    from app.startup import run_pending_migrations

    with sqlite3.connect(bootstrapped_db) as conn:
        before = conn.execute("SELECT COUNT(*) FROM RolePermission").fetchone()[0]

    run_pending_migrations()

    with sqlite3.connect(bootstrapped_db) as conn:
        after = conn.execute("SELECT COUNT(*) FROM RolePermission").fetchone()[0]
    assert after == before
