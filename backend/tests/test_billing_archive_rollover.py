"""Batch 71 — Billing annual lifecycle & rollover contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_invoice_lifecycle_fields_are_declared():
    from app.models.invoice import Invoice

    assert hasattr(Invoice, "invoice_year")
    assert hasattr(Invoice, "storage_tier")
    assert hasattr(Invoice, "is_current_year")


def test_payment_lifecycle_fields_are_declared():
    from app.models.payment import Payment

    assert hasattr(Payment, "payment_year")
    assert hasattr(Payment, "storage_tier")
    assert hasattr(Payment, "is_current_year")


def test_billing_archive_reference_models_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "billing_archive_reference.py"
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0022_billing_operational_year_lifecycle.py"
    )
    assert model.is_file()
    assert migration.is_file()
    text = model.read_text(encoding="utf-8")
    assert "class InvoiceArchiveReference" in text
    assert "class PaymentArchiveReference" in text
    assert "original_invoice_id" in text
    assert "original_payment_id" in text
    assert "archive_manifest_id" in text
    migration_text = migration.read_text(encoding="utf-8")
    assert "invoice_year" in migration_text
    assert "payment_year" in migration_text


def test_billing_archive_references_are_registered():
    init = (ROOT / "backend" / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "InvoiceArchiveReference" in init
    assert "PaymentArchiveReference" in init


def test_billing_service_derives_lifecycle_fields():
    service = (ROOT / "backend" / "app" / "services" / "billing.py").read_text(
        encoding="utf-8"
    )
    assert "invoice_year" in service
    assert "payment_year" in service
    assert 'storage_tier="live"' in service
    assert "is_current_year" in service


def test_billing_read_schemas_expose_lifecycle_fields():
    schema = (ROOT / "backend" / "app" / "schemas" / "billing.py").read_text(
        encoding="utf-8"
    )
    assert "invoice_year: int" in schema
    assert "payment_year: int" in schema
    assert "storage_tier: str" in schema
    assert "is_current_year: bool" in schema


def test_archive_manager_handles_billing_rollover():
    manager = (ROOT / "backend" / "app" / "services" / "archive_manager.py").read_text(
        encoding="utf-8"
    )
    assert "InvoiceArchiveReference(" in manager
    assert "PaymentArchiveReference(" in manager
    assert "invoices_archived" in manager
    assert "payments_archived" in manager
    assert "live_invoice_remaining" in manager
    assert "live_payment_remaining" in manager
    assert "async def read_invoices" in manager
    assert "async def read_payments" in manager
    # Archived billing rows must be physically removed only after references exist.
    assert "delete(Invoice).where(Invoice.id.in_(invoice_ids))" in manager
    assert "delete(Payment).where(Payment.id.in_(payment_ids))" in manager


def test_billing_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    assert '@router.get("/archives/{year}/patients/{patient_id}/invoices")' in maintenance
    assert '@router.get("/archives/{year}/patients/{patient_id}/payments")' in maintenance
    assert "archive_manager.read_invoices" in maintenance
    assert "archive_manager.read_payments" in maintenance
    assert "getHistoricalArchiveInvoices" in api
    assert "getHistoricalArchivePayments" in api
