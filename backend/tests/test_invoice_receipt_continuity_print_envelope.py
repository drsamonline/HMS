"""Batch 92 contract tests — Invoice Receipt Continuity Print Envelope.

These tests lock the reporting/printing integration for the invoice-to-receipt
continuity audit rolled out in Batch 87 (same parity pattern as the aging
ledger in Batch 91):

* The audit derivation is extracted into shared helpers
  (``_load_continuity_scan_inputs`` + ``build_invoice_receipt_continuity_result``)
  used by *both* the dashboard feed and the print envelope, so printed audit
  packets can never drift from screen.
* ``POST /reports/invoice-receipt-continuity-print-envelope`` reuses the same
  live scan (single grouped Payment pass, stored counters never trusted).
* Print schemas expose stable issue lines plus headline aggregates including
  ``issue_count``; every aggregate sums back to ``invoices_checked``.
* Frontend: api wrapper, envelope-aware continuity renderer with
  dashboard-payload fallback, and the Reports workspace card now prepares the
  packet through the print envelope.
* Documentation exists and is indexed in docs/INDEX.md.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_shared_continuity_helpers_extracted_in_dashboard_module():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # one implementation of the scan and the audit, exported for the service
    assert "async def _load_continuity_scan_inputs(" in src
    assert "def build_invoice_receipt_continuity_result(" in src
    # the dashboard endpoint delegates to both instead of scanning inline
    dash = src[src.index('"/invoice-receipt-continuity"'):]
    assert "await _load_continuity_scan_inputs(db, limit)" in dash
    assert "**build_invoice_receipt_continuity_result(" in dash
    # the scan helper itself performs exactly one grouped Payment pass (no N+1)
    scan = src[
        src.index("async def _load_continuity_scan_inputs("):
    ]
    scan = scan[:scan.index("@router.get", 10)] if "@router.get" in scan[10:] else scan
    assert scan.count("Payment.invoice_id.in_(invoice_ids)") == 1
    # cancelled invoices excluded inside the shared scan helper
    assert 'Invoice.payment_status != "cancelled"' in scan
    # Batch 92 docstring entry records the extraction
    assert "Batch 92" in src[:src.index("from __future__")]


def test_print_envelope_endpoint_and_service_share_the_derivation():
    ep = _read("backend/app/api/v1/endpoints/reporting.py")
    assert '"/invoice-receipt-continuity-print-envelope"' in ep
    assert "InvoiceReceiptContinuityPrintEnvelope" in ep
    svc = _read("backend/app/services/reporting.py")
    assert "async def build_invoice_receipt_continuity_print_envelope(" in svc
    # reuses the dashboard's shared helpers — no second audit implementation
    fn = svc[svc.index("def build_invoice_receipt_continuity_print_envelope"):]
    fn = fn[:fn.index("async def", 10)] if "async def" in fn[10:] else fn
    assert "_load_continuity_scan_inputs" in fn
    assert "build_invoice_receipt_continuity_result" in fn
    # envelope carries the convenience issue_count derived from the audit rows
    assert 'issue_count=len(audit["issues"])' in fn
    assert 'InvoiceReceiptGapPrintLine(**issue) for issue in audit["issues"]' in fn


def test_reporting_schemas_expose_continuity_print_envelope():
    src = _read("backend/app/schemas/reporting.py")
    assert "class InvoiceReceiptContinuityPrintRequest(BaseSchema):" in src
    assert "limit: int = Field(default=200, ge=1, le=500)" in src
    for cls in (
        "InvoiceReceiptGapPrintLine",
        "InvoiceReceiptContinuityPrintData",
        "InvoiceReceiptContinuityPrintEnvelope",
    ):
        assert f"class {cls}(BaseSchema):" in src
    # stable printed shape: every defect row mirrors the dashboard item
    for field in (
        "invoice_number",
        "patient_name",
        "gap_type",
        "expected_count",
        "actual_count",
        "missing_count",
        "first_receipt_number",
        "last_receipt_number",
        "duplicate_receipt_numbers",
    ):
        assert field in src
    # headline aggregates + issue_count on the data page
    for field in (
        "invoices_checked",
        "invoices_with_receipts",
        "invoices_missing_receipts",
        "duplicate_receipt_count",
        "sequence_break_count",
        "issue_count",
    ):
        assert field in src
    assert 'report_type: Literal["invoice_receipt_continuity_print"]' in src
    exports = src.split("__all__")[-1]
    for name in (
        "InvoiceReceiptContinuityPrintRequest",
        "InvoiceReceiptGapPrintLine",
        "InvoiceReceiptContinuityPrintData",
        "InvoiceReceiptContinuityPrintEnvelope",
    ):
        assert name in exports


def test_api_wrapper_posts_continuity_print_envelope():
    api = _read("frontend/js/api.js")
    assert "buildInvoiceReceiptContinuityPrintEnvelope" in api
    assert "/api/v1/reports/invoice-receipt-continuity-print-envelope" in api
    assert 'method:"POST"' in api[
        api.index("buildInvoiceReceiptContinuityPrintEnvelope"):
    ][:220]


def test_print_renderer_accepts_envelope_with_dashboard_fallback():
    prn = _read("frontend/js/print.js")
    fn = prn[prn.index("export function createInvoiceReceiptContinuityPrintPreview"):]
    fn = fn[:fn.index("\nexport function", 10)] if "\nexport function" in fn[10:] else fn
    # envelope-first with backward-compatible dashboard-payload fallback
    assert "{envelope=null,data=null" in fn
    assert "const src=envelope?.data??data??{};" in fn
    assert "envelope?.title||title" in fn
    # all rendered aggregates read from src, never the raw data arg
    assert "src?.invoices_checked" in fn
    assert "src?.invoices_with_receipts" in fn
    assert "src?.invoices_missing_receipts" in fn
    assert "src?.duplicate_receipt_count" in fn
    assert "src?.sequence_break_count" in fn
    # sections keep the stable printed shape
    assert "Continuity Summary" in fn
    assert "Continuity Issues" in fn
    assert "return {envelope,src};" in fn


def test_reports_workspace_prepares_continuity_through_envelope():
    rep = _read("frontend/js/reports.js")
    assert "buildInvoiceReceiptContinuityPrintEnvelope" in rep
    # the card now goes through the print envelope, not the dashboard feed
    assert "getDashboardInvoiceReceiptContinuity" not in rep
    handler = rep[rep.index("#continuity-prepare"):]
    handler = handler[:handler.index("\n")]
    assert (
        'buildInvoiceReceiptContinuityPrintEnvelope({limit,title:"Invoice Receipt Continuity Report"})'
        in handler
    )
    assert (
        'createInvoiceReceiptContinuityPrintPreview($("#print-preview-host",box),{envelope:env})'
        in handler
    )
    # status line reports envelope headline aggregates (issue_count, not .length)
    assert "${d.invoices_checked} invoice(s) checked, ${d.issue_count} issue(s)" in handler
    # ids render as plain attributes (no escaped-quote regression, Batch 89 lesson)
    assert 'id=\\"continuity-limit\\"' in rep  # single-escaped convention inside template literal
    assert 'id=\\"continuity-prepare\\"' in rep
    assert 'id=\\"continuity-note\\"' in rep


def test_batch92_documentation_exists_and_indexed():
    doc = _read("docs/CLIENT_INVOICE_RECEIPT_CONTINUITY_PRINT_ENVELOPE.md")
    assert "Batch 92" in doc
    assert "/reports/invoice-receipt-continuity-print-envelope" in doc
    assert "build_invoice_receipt_continuity_result" in doc
    assert "_load_continuity_scan_inputs" in doc
    index = _read("docs/INDEX.md")
    assert "CLIENT_INVOICE_RECEIPT_CONTINUITY_PRINT_ENVELOPE.md" in index
