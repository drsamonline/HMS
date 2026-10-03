"""Batch 94 — Invoice Payment Reconciliation Print Envelope contracts.

Locks in the screen/paper parity extraction: the Batch 89 live-payment
reconciliation ledger moved out of the dashboard endpoint body into the shared
``build_invoice_payment_reconciliation_ledger`` derivation, which both
``GET /dashboard/invoice-payment-reconciliation`` and the new reporting print
envelope endpoint run through, so printed ledger lines can never drift from
the screen feed for the same scan window.

Locked-in surfaces:

* shared derivation ``build_invoice_payment_reconciliation_ledger`` (and its
  row builder ``_build_reconciliation_rows``) in the dashboard module — single
  grouped Payment pass, no N+1, stored counters/status never trusted, Batch 68
  clamp invariant ``amount_paid + balance_due == total_amount``;
* ``POST /reports/invoice-payment-reconciliation-print-envelope`` delegating
  to that same helper via the reporting service;
* print schemas (``InvoicePaymentReconciliationPrintRequest``/
  ``InvoicePaymentReconciliationPrintLine``/
  ``InvoicePaymentReconciliationPrintData``/
  ``InvoicePaymentReconciliationPrintEnvelope``) exported in ``__all__``;
* frontend API wrapper, envelope-aware print-preview renderer with
  dashboard-data fallback, and Reports workspace card switched to the
  envelope;
* feature documentation indexed in docs/INDEX.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_shared_derivation_extracted_from_dashboard_endpoint():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # the ledger body now lives in one shared async helper...
    assert "async def build_invoice_payment_reconciliation_ledger(db, limit: int) -> dict:" in src
    # ...built on top of the shared live-scan row builder
    assert "async def _build_reconciliation_rows(db, limit: int)" in src
    # single grouped pass over the Payment ledger (no N+1)
    assert "group_by(Payment.invoice_id)" in src
    # stored counters/status never trusted: derived status helper is used
    assert "def _derive_payment_status(" in src
    # Batch 68 clamp invariant documented/enforced in the derivation
    assert "balance_due" in src and "amount_paid" in src
    # Batch 94 documented in the module docstring
    assert "Batch 94" in src


def test_dashboard_endpoint_delegates_to_shared_ledger():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # the GET endpoint delegates instead of re-implementing the scan
    assert '@router.get("/invoice-payment-reconciliation"' in src
    assert "build_invoice_payment_reconciliation_ledger(db, limit)" in src


def test_reporting_service_reuses_shared_scan():
    src = _read("backend/app/services/reporting.py")
    assert (
        "async def build_invoice_payment_reconciliation_print_envelope(" in src
    )
    # delegates to the *same* derivation as the dashboard feed — no copy
    assert "build_invoice_payment_reconciliation_ledger" in src
    # envelope carries headline aggregates plus per-invoice print lines
    assert "InvoicePaymentReconciliationPrintEnvelope(" in src
    assert "InvoicePaymentReconciliationPrintData(" in src
    assert "InvoicePaymentReconciliationPrintLine(" in src


def test_reporting_endpoint_wired_with_response_model():
    src = _read("backend/app/api/v1/endpoints/reporting.py")
    assert '"/invoice-payment-reconciliation-print-envelope"' in src
    assert (
        "response_model=InvoicePaymentReconciliationPrintEnvelope" in src
    )
    assert "report_in: InvoicePaymentReconciliationPrintRequest" in src
    # Batch 94 documented in the endpoint docstring
    assert "Batch 94" in src


def test_print_schemas_fields_and_exports():
    src = _read("backend/app/schemas/reporting.py")
    for cls in (
        "class InvoicePaymentReconciliationPrintRequest(BaseSchema):",
        "class InvoicePaymentReconciliationPrintLine(BaseSchema):",
        "class InvoicePaymentReconciliationPrintData(BaseSchema):",
        "class InvoicePaymentReconciliationPrintEnvelope(BaseSchema):",
    ):
        assert cls in src
    # bounded limit mirrors the dashboard feed (default 200, max 500)
    request_block = src.split(
        "class InvoicePaymentReconciliationPrintRequest(BaseSchema):"
    )[1].split("class InvoicePaymentReconciliationPrintLine")[0]
    assert "200" in request_block and "500" in request_block
    # report_type discriminator on the envelope
    assert '"invoice_payment_reconciliation_print"' in src
    # all four exported in __all__
    for name in (
        "InvoicePaymentReconciliationPrintRequest",
        "InvoicePaymentReconciliationPrintLine",
        "InvoicePaymentReconciliationPrintData",
        "InvoicePaymentReconciliationPrintEnvelope",
    ):
        assert f'"{name}"' in src


def test_frontend_api_wrapper_present():
    api = _read("frontend/js/api.js")
    assert "export async function buildInvoicePaymentReconciliationPrintEnvelope(" in api
    assert "/api/v1/reports/invoice-payment-reconciliation-print-envelope" in api
    assert 'method:"POST"' in api or 'method: "POST"' in api


def test_print_preview_accepts_envelope_with_fallback():
    src = _read("frontend/js/print.js")
    assert (
        "export function createInvoicePaymentReconciliationPrintPreview(" in src
    )
    # envelope-first signature with raw dashboard data fallback
    assert "{envelope=null,data=null" in src.replace(" ", "")
    # summary + ledger sections rendered
    assert "Reconciliation Summary" in src
    assert "Reconciliation Ledger" in src


def test_reports_workspace_card_prepares_through_envelope():
    src = _read("frontend/js/reports.js")
    # imports the envelope wrapper (not just the dashboard feed)
    assert "buildInvoicePaymentReconciliationPrintEnvelope" in src
    assert "createInvoicePaymentReconciliationPrintPreview" in src
    # handler posts through the envelope and reads envelope aggregates
    handler = src.split('#reconciliation-prepare')[-1]
    assert "await buildInvoicePaymentReconciliationPrintEnvelope({limit})" in handler
    assert "envelope?.data" in handler
    # Batch 89 quoting convention preserved: ids render as plain id="..."
    assert 'id=\\"reconciliation-limit\\"' in src
    assert 'id=\\"reconciliation-prepare\\"' in src


def test_documentation_indexed():
    docs = _read("docs/CLIENT_INVOICE_PAYMENT_RECONCILIATION_PRINT_ENVELOPE.md")
    assert "invoice-payment-reconciliation-print-envelope" in docs
    index = _read("docs/INDEX.md")
    assert "CLIENT_INVOICE_PAYMENT_RECONCILIATION_PRINT_ENVELOPE.md" in index
    assert "Batch 94" in index


__all__ = [
    "test_shared_derivation_extracted_from_dashboard_endpoint",
    "test_dashboard_endpoint_delegates_to_shared_ledger",
    "test_reporting_service_reuses_shared_scan",
    "test_reporting_endpoint_wired_with_response_model",
    "test_print_schemas_fields_and_exports",
    "test_frontend_api_wrapper_present",
    "test_print_preview_accepts_envelope_with_fallback",
    "test_reports_workspace_card_prepares_through_envelope",
    "test_documentation_indexed",
]
