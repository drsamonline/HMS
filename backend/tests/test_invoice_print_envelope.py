"""Batch 85 — Invoice Print Envelope contracts (final reporting/printing integration).

Locks in the surfaces that turn a stored invoice into a complete, printable
document packet:

* ``ReportingService.build_invoice_print_envelope`` assembles header, line
  items and receipts with balances derived from live payments (never the
  stored status alone) and clamped so the printed figures always reconcile:
  ``total_amount == amount_paid + balance_due`` with both sides >= 0,
* a dedicated POST /reports/invoice-print-envelope endpoint registered on
  the reporting router with authenticated access,
* response schemas exposing the printable fields,
* frontend API wrapper plus invoice print preview rendering wired into the
  Reports & Printing workspace.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_reporting_service_builds_invoice_print_envelope():
    src = _read("backend/app/services/reporting.py")
    assert "async def build_invoice_print_envelope" in src
    # invoice header, line items and receipts all come from live rows
    assert "InvoiceItem.invoice_id == invoice.id" in src
    assert "Payment.invoice_id == invoice.id" in src
    # Batch 68 semantics: balances derived from payments, not stored status
    assert 'paid_total = sum((Decimal(str(row.amount_paid)) for row in receipts), Decimal("0"))' in src
    assert "amount_paid = min(paid_total, total_amount)" in src
    assert "balance_due = max(total_amount - amount_paid, Decimal(\"0\"))" in src
    # missing invoice must fail loudly instead of printing an empty sheet
    assert 'ResourceNotFoundException("Invoice not found.")' in src


def test_invoice_print_endpoint_registered_on_reporting_router():
    src = _read("backend/app/api/v1/endpoints/reporting.py")
    assert 'prefix="/reports"' in src
    assert '"/invoice-print-envelope"' in src
    assert "response_model=InvoicePrintEnvelope" in src
    assert "reporting_service.build_invoice_print_envelope" in src
    assert "CurrentUserDependency" in src


def test_invoice_print_schemas_expose_printable_fields():
    src = _read("backend/app/schemas/reporting.py")
    for cls in (
        "class InvoicePrintRequest",
        "class InvoicePrintItemLine",
        "class InvoicePrintReceiptLine",
        "class InvoicePrintData",
        "class InvoicePrintEnvelope",
    ):
        assert cls in src
    for field in ("total_amount", "amount_paid", "balance_due", "payment_status"):
        assert field in src
    assert 'Literal["invoice_print"]' in src
    # invoice_id validated positive like every other report scope id
    assert "invoice_id: int = Field(gt=0)" in src


def test_frontend_wrapper_preview_and_workspace_wiring():
    api = _read("frontend/js/api.js")
    print_js = _read("frontend/js/print.js")
    reports = _read("frontend/js/reports.js")
    assert "/api/v1/reports/invoice-print-envelope" in api
    assert "buildInvoicePrintEnvelope" in api
    assert "export function createInvoicePrintPreview" in print_js
    # preview shows the reconciling figures a cashier signs off against
    for label in ("Total Amount", "Amount Paid", "Balance Due", "Receipts", "Line Items"):
        assert label in print_js
    assert "createInvoicePrintPreview" in reports
    assert "buildInvoicePrintEnvelope" in reports
    assert "invoice-print-prepare" in reports
    assert "invoice-print-id" in reports


def test_invoice_print_request_schema_validation():
    from app.schemas.reporting import InvoicePrintEnvelope, InvoicePrintRequest

    request = InvoicePrintRequest(invoice_id=7, title="Final Invoice")
    assert request.invoice_id == 7
    assert request.title == "Final Invoice"

    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        InvoicePrintRequest(invoice_id=0)

    envelope = InvoicePrintEnvelope.model_validate(
        {
            "title": "HHMS Invoice INV-0001",
            "generated_at": "2026-10-03T00:00:00Z",
            "invoice_id": 1,
            "invoice_number": "INV-0001",
            "patient_id": 2,
            "data": {
                "invoice": {"id": 1},
                "items": [],
                "receipts": [],
                "patient": {"id": 2},
                "total_amount": "100.00",
                "amount_paid": "40.00",
                "balance_due": "60.00",
                "payment_status": "partial",
                "generated_at": "2026-10-03T00:00:00Z",
            },
        }
    )
    assert envelope.report_type == "invoice_print"
    # printed packet must reconcile exactly
    from decimal import Decimal

    assert Decimal(envelope.data.total_amount) == Decimal(envelope.data.amount_paid) + Decimal(
        envelope.data.balance_due
    )
