"""Batch 87 — Invoice Receipt Continuity Report contracts.

Locks in the surfaces that audit invoice-to-receipt numbering integrity on
live billing data and expose it for reporting/printing:

* GET /dashboard/invoice-receipt-continuity scanning recent invoices with a
  single grouped pass over Payment receipts (no N+1), never trusting stored
  counters,
* stable gap taxonomy — missing / duplicate / sequence_break — derived from
  receipt-number structure (numeric-suffix span analysis via
  ``_receipt_numeric_suffix``),
* "missing" detection consistent with the Batch 82 live-payment derivation
  (payments recorded or partial/paid status but zero linked receipts),
* response schema exposing headline aggregates plus per-invoice issue rows
  whose counts sum back to ``invoices_checked`` so printed audits reconcile,
* frontend API wrapper, continuity print-preview renderer, and Reports &
  Printing workspace card wired end-to-end.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dashboard_endpoint_exposes_invoice_receipt_continuity():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/invoice-receipt-continuity"' in src
    assert "response_model=InvoiceReceiptContinuityResponse" in src
    assert "CurrentUserDependency" in src
    # limit is bounded like every other dashboard feed (1..500)
    assert "Query(default=200, ge=1, le=500)" in src


def test_continuity_scans_live_invoices_without_trusting_counters():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # cancelled invoices are excluded from the audit scope
    assert 'Invoice.payment_status != "cancelled"' in src
    # most-recent-first scan window, deterministic ordering
    assert "Invoice.invoice_date.desc(), Invoice.id.desc()" in src
    # receipts come from a single grouped query over the Payment ledger
    assert "Payment.invoice_id.in_(invoice_ids)" in src
    assert "Payment.receipt_number" in src
    assert "Payment.amount_paid" in src
    # ordered by payment time then id so first/last receipt numbers are stable
    assert "Payment.payment_datetime.asc(), Payment.id.asc()" in src


def test_gap_taxonomy_is_stable_and_span_based():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # the three audited defect classes
    assert '"gap_type": "missing"' in src
    assert '"gap_type": "duplicate"' in src
    assert '"gap_type": "sequence_break"' in src
    # numeric-suffix extraction helper gates which series can be span-checked
    assert "_receipt_numeric_suffix" in src
    # duplicates detected within an invoice's own receipt list
    assert "numbers.count(n) > 1" in src
    # sequence breaks computed from the unique-suffix span, not raw counts
    assert "expected_span = unique_sorted[-1] - unique_sorted[0] + 1" in src
    assert "missing_in_span = expected_span - len(unique_sorted)" in src


def test_missing_receipt_detection_follows_batch82_payment_semantics():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # paid is derived from live payments, mirroring Batch 82 outstanding logic
    assert "paid_by_invoice.get(invoice.id, Decimal(\"0\"))" in src
    assert "paid > 0" in src
    assert 'str(invoice.payment_status) in ("partial", "paid")' in src


def test_continuity_schemas_expose_aggregates_and_issue_rows():
    src = _read("backend/app/schemas/dashboard.py")
    for cls in (
        "class InvoiceReceiptGapItem",
        "class InvoiceReceiptContinuityResponse",
    ):
        assert cls in src
    for field in (
        "invoices_checked",
        "invoices_with_receipts",
        "invoices_missing_receipts",
        "duplicate_receipt_count",
        "sequence_break_count",
        "gap_type",
        "expected_count",
        "actual_count",
        "missing_count",
        "first_receipt_number",
        "last_receipt_number",
        "duplicate_receipt_numbers",
    ):
        assert field in src
    # exported so the endpoint can import them
    tail = src.split("__all__")[-1]
    assert "InvoiceReceiptGapItem" in tail
    assert "InvoiceReceiptContinuityResponse" in tail


def test_frontend_wrapper_calls_invoice_receipt_continuity_endpoint():
    api = _read("frontend/js/api.js")
    assert "getDashboardInvoiceReceiptContinuity" in api
    assert "/api/v1/dashboard/invoice-receipt-continuity" in api
    assert "limit:String(options.limit??200)" in api


def test_print_preview_renders_continuity_summary_and_issues():
    print_js = _read("frontend/js/print.js")
    assert "createInvoiceReceiptContinuityPrintPreview" in print_js
    # headline aggregates all present in the summary table
    for token in (
        "Invoices checked",
        "Invoices with receipts",
        "Invoices missing receipts",
        "Duplicate receipt numbers",
        "Sequence breaks",
    ):
        assert token in print_js
    # issues table with reconciliation columns and clean-book fallback
    assert "data-print-section=\"issues\"" in print_js
    assert "No continuity issues detected" in print_js


def test_reports_workspace_wires_continuity_card_end_to_end():
    reports = _read("frontend/js/reports.js")
    # Batch 92 — the card now goes through the print envelope, not the raw
    # dashboard feed (same parity switch as the aging card in Batch 91).
    assert "buildInvoiceReceiptContinuityPrintEnvelope" in reports
    assert "createInvoiceReceiptContinuityPrintPreview" in reports
    assert "Invoice receipt continuity report" in reports
    assert "continuity-limit" in reports
    assert "continuity-prepare" in reports
    # status line reports checks and issue count for operator confidence
    assert "invoices_checked" in reports
    assert "issue_count" in reports
