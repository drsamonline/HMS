"""Batch 74 — Laboratory investigation annual lifecycle & rollover contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_investigation_lifecycle_fields_are_declared():
    from app.models.investigation import Investigation

    assert hasattr(Investigation, "investigation_year")
    assert hasattr(Investigation, "storage_tier")
    assert hasattr(Investigation, "is_current_year")


def test_investigation_result_lifecycle_fields_are_declared():
    from app.models.investigation_result import InvestigationResult

    assert hasattr(InvestigationResult, "result_year")
    assert hasattr(InvestigationResult, "storage_tier")
    assert hasattr(InvestigationResult, "is_current_year")


def test_lab_archive_reference_model_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "lab_archive_reference.py"
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0025_lab_operational_year_lifecycle.py"
    )
    assert model.is_file()
    assert migration.is_file()
    text = model.read_text(encoding="utf-8")
    assert "class InvestigationArchiveReference" in text
    assert "original_investigation_id" in text
    assert "archive_manifest_id" in text
    assert "uq_investigation_archive_ref_original_investigation" in text
    migration_text = migration.read_text(encoding="utf-8")
    assert "investigation_year" in migration_text
    assert "result_year" in migration_text
    assert "storage_tier" in migration_text
    assert "is_current_year" in migration_text
    assert "InvestigationArchiveReference" in migration_text


def test_lab_archive_reference_is_registered():
    init = (ROOT / "backend" / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "InvestigationArchiveReference" in init


def test_investigation_service_derives_lifecycle_fields():
    service = (ROOT / "backend" / "app" / "services" / "investigation.py").read_text(
        encoding="utf-8"
    )
    assert "operational_year_service" in service
    assert "investigation_year=investigation_year" in service
    assert 'storage_tier="live"' in service
    assert "is_current_year=investigation_year == current_year" in service


def test_investigation_result_service_derives_lifecycle_fields():
    service = (
        ROOT / "backend" / "app" / "services" / "investigation_result.py"
    ).read_text(encoding="utf-8")
    assert "operational_year_service" in service
    assert "result_year=result_year" in service


def test_investigation_read_schemas_expose_lifecycle_fields():
    schema = (ROOT / "backend" / "app" / "schemas" / "investigation.py").read_text(
        encoding="utf-8"
    )
    assert "investigation_year: int" in schema
    assert "storage_tier: str | None" in schema
    assert "is_current_year: bool | None" in schema
    result_schema = (
        ROOT / "backend" / "app" / "schemas" / "investigation_result.py"
    ).read_text(encoding="utf-8")
    assert "result_year: int" in result_schema
    assert "storage_tier: str | None" in result_schema
    assert "is_current_year: bool | None" in result_schema


def test_archive_manager_handles_lab_rollover():
    manager = (ROOT / "backend" / "app" / "services" / "archive_manager.py").read_text(
        encoding="utf-8"
    )
    assert "InvestigationArchiveReference(" in manager
    assert "investigations_archived" in manager
    assert "investigation_count" in manager
    assert "live_investigation_remaining" in manager
    assert "async def read_investigations" in manager
    # Results are removed with their parent investigations; both only after
    # archive references exist.
    assert "delete(InvestigationResult).where(" in manager
    assert "delete(Investigation).where(Investigation.id.in_(investigation_ids))" in manager


def test_lab_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    assert '@router.get("/archives/{year}/patients/{patient_id}/investigations")' in maintenance
    assert "archive_manager.read_investigations" in maintenance
    assert "getHistoricalArchiveInvestigations" in api
