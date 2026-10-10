"""Batch 72 — Pharmacy dispense annual lifecycle & rollover contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dispense_lifecycle_fields_are_declared():
    from app.models.dispense_record import DispenseRecord

    assert hasattr(DispenseRecord, "dispense_year")
    assert hasattr(DispenseRecord, "storage_tier")
    assert hasattr(DispenseRecord, "is_current_year")


def test_dispense_prescription_item_link_is_detachable():
    """Dispense rows must survive prescription-item rollover (nullable FK)."""
    from app.models.dispense_record import DispenseRecord

    column = DispenseRecord.__table__.columns["prescription_item_id"]
    assert column.nullable is True


def test_pharmacy_archive_reference_model_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "pharmacy_archive_reference.py"
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0023_pharmacy_operational_year_lifecycle.py"
    )
    assert model.is_file()
    assert migration.is_file()
    text = model.read_text(encoding="utf-8")
    assert "class DispenseArchiveReference" in text
    assert "original_dispense_id" in text
    assert "archive_manifest_id" in text
    assert "uq_dispense_archive_ref_original_dispense" in text
    migration_text = migration.read_text(encoding="utf-8")
    assert "dispense_year" in migration_text
    assert "storage_tier" in migration_text
    assert "is_current_year" in migration_text
    assert "DispenseArchiveReference" in migration_text


def test_pharmacy_archive_reference_is_registered():
    init = (ROOT / "backend" / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "DispenseArchiveReference" in init


def test_dispense_service_derives_lifecycle_fields():
    service = (ROOT / "backend" / "app" / "services" / "dispense.py").read_text(
        encoding="utf-8"
    )
    assert "operational_year_service" in service
    assert "dispense_year=dispense_year" in service
    assert 'storage_tier="live"' in service
    assert "is_current_year=dispense_year == current_year" in service


def test_dispense_read_schema_exposes_lifecycle_fields():
    schema = (ROOT / "backend" / "app" / "schemas" / "dispense.py").read_text(
        encoding="utf-8"
    )
    assert "dispense_year: int | None" in schema
    assert "storage_tier: str | None" in schema
    assert "is_current_year: bool | None" in schema


def test_archive_manager_handles_pharmacy_rollover():
    manager = (ROOT / "backend" / "app" / "services" / "archive_manager.py").read_text(
        encoding="utf-8"
    )
    assert "DispenseArchiveReference(" in manager
    assert "dispenses_archived" in manager
    assert "dispense_count" in manager
    assert "live_dispense_remaining" in manager
    assert "async def read_dispenses" in manager
    # Archived dispense rows must be physically removed only after references exist.
    assert "delete(DispenseRecord).where(DispenseRecord.id.in_(dispense_ids))" in manager


def test_pharmacy_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    assert '@router.get("/archives/{year}/patients/{patient_id}/dispenses")' in maintenance
    assert "archive_manager.read_dispenses" in maintenance
    assert "getHistoricalArchiveDispenses" in api
