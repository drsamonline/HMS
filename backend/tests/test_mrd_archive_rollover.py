"""Batch 75 — MRD medical-document annual lifecycle & rollover contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_medical_document_lifecycle_fields_are_declared():
    from app.models.medical_document import MedicalDocument

    assert hasattr(MedicalDocument, "document_year")
    assert hasattr(MedicalDocument, "storage_tier")
    assert hasattr(MedicalDocument, "is_current_year")


def test_mrd_archive_reference_model_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "mrd_archive_reference.py"
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0026_mrd_operational_year_lifecycle.py"
    )
    assert model.is_file()
    assert migration.is_file()
    text = model.read_text(encoding="utf-8")
    assert "class MedicalDocumentArchiveReference" in text
    assert "original_document_id" in text
    assert "archive_manifest_id" in text
    assert "uq_medical_document_archive_ref_original_document" in text
    migration_text = migration.read_text(encoding="utf-8")
    assert "document_year" in migration_text
    assert "storage_tier" in migration_text
    assert "is_current_year" in migration_text
    assert "MedicalDocumentArchiveReference" in migration_text


def test_mrd_archive_reference_is_registered():
    init = (ROOT / "backend" / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "MedicalDocumentArchiveReference" in init


def test_medical_document_service_derives_lifecycle_fields():
    service = (
        ROOT / "backend" / "app" / "services" / "medical_document.py"
    ).read_text(encoding="utf-8")
    assert "operational_year_service" in service
    assert "document_year=document_year" in service
    assert 'storage_tier="live"' in service
    assert "is_current_year=document_year == current_year" in service


def test_medical_document_read_schema_exposes_lifecycle_fields():
    schema = (ROOT / "backend" / "app" / "schemas" / "medical_document.py").read_text(
        encoding="utf-8"
    )
    assert "document_year: int | None" in schema
    assert "storage_tier: str | None" in schema
    assert "is_current_year: bool | None" in schema


def test_archive_manager_handles_mrd_rollover():
    manager = (ROOT / "backend" / "app" / "services" / "archive_manager.py").read_text(
        encoding="utf-8"
    )
    assert "MedicalDocumentArchiveReference(" in manager
    assert "documents_archived" in manager
    assert "document_count" in manager
    assert "live_document_remaining" in manager
    assert "async def read_documents" in manager
    # Archived document rows must be physically removed only after references exist.
    assert "delete(MedicalDocument).where(" in manager


def test_mrd_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    assert '@router.get("/archives/{year}/patients/{patient_id}/documents")' in maintenance
    assert "archive_manager.read_documents" in maintenance
    assert "getHistoricalArchiveDocuments" in api
