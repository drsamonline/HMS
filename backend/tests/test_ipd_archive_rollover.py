"""Batch 73 — IPD admission annual lifecycle & rollover contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_admission_lifecycle_fields_are_declared():
    from app.models.admission import Admission

    assert hasattr(Admission, "admission_year")
    assert hasattr(Admission, "storage_tier")
    assert hasattr(Admission, "is_current_year")


def test_ipd_archive_reference_model_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "admission_archive_reference.py"
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0024_ipd_operational_year_lifecycle.py"
    )
    assert model.is_file()
    assert migration.is_file()
    text = model.read_text(encoding="utf-8")
    assert "class AdmissionArchiveReference" in text
    assert "original_admission_id" in text
    assert "archive_manifest_id" in text
    assert "uq_admission_archive_ref_original_admission" in text
    migration_text = migration.read_text(encoding="utf-8")
    assert "admission_year" in migration_text
    assert "storage_tier" in migration_text
    assert "is_current_year" in migration_text
    assert "AdmissionArchiveReference" in migration_text


def test_ipd_archive_reference_is_registered():
    init = (ROOT / "backend" / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "AdmissionArchiveReference" in init


def test_admission_service_derives_lifecycle_fields():
    service = (ROOT / "backend" / "app" / "services" / "admission.py").read_text(
        encoding="utf-8"
    )
    assert "operational_year_service" in service
    assert "admission_year=admission_year" in service
    assert 'storage_tier="live"' in service
    assert "is_current_year=admission_year == current_year" in service


def test_admission_read_schema_exposes_lifecycle_fields():
    schema = (ROOT / "backend" / "app" / "schemas" / "admission.py").read_text(
        encoding="utf-8"
    )
    assert "admission_year: int | None" in schema
    assert "storage_tier: str | None" in schema
    assert "is_current_year: bool | None" in schema


def test_archive_manager_handles_ipd_rollover():
    manager = (ROOT / "backend" / "app" / "services" / "archive_manager.py").read_text(
        encoding="utf-8"
    )
    assert "AdmissionArchiveReference(" in manager
    assert "admissions_archived" in manager
    assert "admission_count" in manager
    assert "live_admission_remaining" in manager
    assert "async def read_admissions" in manager
    # Archived admission rows must be physically removed only after references exist.
    assert "delete(Admission).where(Admission.id.in_(admission_ids))" in manager


def test_ipd_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    assert '@router.get("/archives/{year}/patients/{patient_id}/admissions")' in maintenance
    assert "archive_manager.read_admissions" in maintenance
    assert "getHistoricalArchiveAdmissions" in api
