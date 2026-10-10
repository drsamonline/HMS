"""Batch 77 — Prescription annual lifecycle & lineage rollover contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_prescription_lifecycle_fields_are_declared():
    from app.models.prescription import Prescription
    from app.models.prescription_item import PrescriptionItem

    assert hasattr(Prescription, "prescription_year")
    assert hasattr(Prescription, "storage_tier")
    assert hasattr(Prescription, "is_current_year")
    assert hasattr(PrescriptionItem, "item_year")
    assert hasattr(PrescriptionItem, "storage_tier")
    assert hasattr(PrescriptionItem, "is_current_year")


def test_prescription_visit_link_is_detachable():
    """Prescriptions must survive visit rollover (nullable FK since 0028)."""
    from app.models.prescription import Prescription

    column = Prescription.__table__.columns["visit_id"]
    assert column.nullable is True


def test_clinical_archive_reference_model_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "clinical_archive_reference.py"
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0028_prescription_operational_year_lifecycle.py"
    )
    assert model.is_file()
    assert migration.is_file()
    text = model.read_text(encoding="utf-8")
    assert "class PrescriptionArchiveReference" in text
    assert "original_prescription_id" in text
    assert "uq_prescription_archive_ref_original_prescription" in text
    assert "class PrescriptionItemArchiveReference" in text
    assert "original_item_id" in text
    assert "uq_prescription_item_archive_ref_original_item" in text
    migration_text = migration.read_text(encoding="utf-8")
    assert "prescription_year" in migration_text
    assert "item_year" in migration_text
    assert "storage_tier" in migration_text
    assert "is_current_year" in migration_text
    assert "PrescriptionArchiveReference" in migration_text
    assert "PrescriptionItemArchiveReference" in migration_text


def test_clinical_archive_references_are_registered():
    init = (ROOT / "backend" / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "PrescriptionArchiveReference" in init
    assert "PrescriptionItemArchiveReference" in init


def test_prescription_service_derives_lifecycle_fields():
    service = (ROOT / "backend" / "app" / "services" / "prescription.py").read_text(
        encoding="utf-8"
    )
    assert "operational_year_service" in service
    assert "prescription_year=prescription_year" in service
    assert "item_year=prescription_year" in service
    assert "is_current_year=prescription_year == current_year" in service


def test_prescription_read_schema_exposes_lifecycle_fields():
    schema = (ROOT / "backend" / "app" / "schemas" / "prescription.py").read_text(
        encoding="utf-8"
    )
    assert "prescription_year: int = 0" in schema
    assert "item_year: int = 0" in schema
    assert 'storage_tier: str = "live"' in schema
    assert "is_current_year: bool = True" in schema
    assert "visit_id: int | None = None" in schema


def test_archive_manager_handles_prescription_rollover():
    manager = (ROOT / "backend" / "app" / "services" / "archive_manager.py").read_text(
        encoding="utf-8"
    )
    assert "PrescriptionArchiveReference(" in manager
    assert "PrescriptionItemArchiveReference(" in manager
    assert "prescriptions_archived" in manager
    assert "prescription_items_archived" in manager
    assert "prescription_count" in manager
    assert "prescription_item_count" in manager
    assert "live_prescription_remaining" in manager
    assert "live_prescription_item_remaining" in manager
    assert "async def read_prescriptions" in manager
    assert "async def read_prescription_items" in manager
    # Archived prescription rows must be physically removed only after
    # references exist and after live dispensing/follow-up pointers detach.
    assert "delete(PrescriptionItem).where(PrescriptionItem.id.in_(archived_item_ids))" in manager or \
           "delete(PrescriptionItem)" in manager
    assert "delete(Prescription).where(Prescription.id.in_(prescription_ids))" in manager
    assert "values(prescription_item_id=None)" in manager
    assert "values(previous_prescription_id=None)" in manager
    assert "values(next_prescription_id=None)" in manager


def test_prescription_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    assert '@router.get("/archives/{year}/patients/{patient_id}/prescriptions")' in maintenance
    assert '@router.get("/archives/{year}/patients/{patient_id}/prescription-items")' in maintenance
    assert "archive_manager.read_prescriptions" in maintenance
    assert "archive_manager.read_prescription_items" in maintenance
    assert "getHistoricalArchivePrescriptions" in api
    assert "getHistoricalArchivePrescriptionItems" in api
