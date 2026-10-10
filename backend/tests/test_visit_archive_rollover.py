"""Batch 70 — Encounter annual lifecycle & rollover contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_visit_lifecycle_fields_are_declared():
    from app.models.visit import Visit

    assert hasattr(Visit, "visit_year")
    assert hasattr(Visit, "storage_tier")
    assert hasattr(Visit, "is_current_year")


def test_visit_archive_reference_model_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "visit_archive_reference.py"
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0021_visit_operational_year_lifecycle.py"
    )
    assert model.is_file()
    assert migration.is_file()
    text = model.read_text(encoding="utf-8")
    assert "class VisitArchiveReference" in text
    assert "original_visit_id" in text
    assert "archive_manifest_id" in text
    assert "Visit" in migration.read_text(encoding="utf-8")


def test_visit_archive_reference_is_registered():
    init = (ROOT / "backend" / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "from .visit_archive_reference import VisitArchiveReference" in init
    assert '"VisitArchiveReference"' in init


def test_visit_service_derives_lifecycle_fields():
    service = (ROOT / "backend" / "app" / "services" / "visit.py").read_text(
        encoding="utf-8"
    )
    assert "visit_year=visit_year" in service
    assert 'storage_tier="live"' in service
    assert "is_current_year=visit_year == current_year" in service


def test_visit_read_schema_exposes_lifecycle_fields():
    schema = (ROOT / "backend" / "app" / "schemas" / "visit.py").read_text(
        encoding="utf-8"
    )
    assert "visit_year: int" in schema
    assert 'storage_tier: str' in schema
    assert "is_current_year: bool" in schema


def test_archive_manager_handles_visit_rollover():
    manager = (ROOT / "backend" / "app" / "services" / "archive_manager.py").read_text(
        encoding="utf-8"
    )
    assert "VisitArchiveReference(" in manager
    assert "visits_archived" in manager
    assert "live_visit_remaining" in manager
    assert "async def read_visits" in manager
    # Archived visits must be physically removed only after references exist.
    assert "delete(Visit).where(Visit.id.in_(visit_ids))" in manager


def test_visit_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    assert '@router.get("/archives/{year}/patients/{patient_id}/visits")' in maintenance
    assert "getHistoricalArchiveVisits" in api
