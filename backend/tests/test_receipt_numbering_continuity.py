"""Batch 88 — Receipt Numbering Continuity Audit contracts.

Extends the Batch 87 invoice-scoped receipt audit to a whole-receipt-book
audit: every receipt number in the ledger is checked against its own numeric
series (the non-digit prefix, e.g. ``R`` in ``R000123``), so billing staff can
see missing numbers, duplicates and sequence breaks across the *entire* book
rather than one invoice at a time.

Locked-in surfaces:

* ``ReceiptNumberingContinuityResponse`` / ``ReceiptSeriesGap`` schemas with
  per-series expected/actual/gap counts that always reconcile
  (``expected_count == actual_count + gap_count``);
* ``GET /dashboard/receipt-numbering-continuity`` scanning live Payment rows
  in a single ordered pass (no N+1), reusing the Batch 87
  ``_receipt_numeric_suffix`` series parsing;
* frontend API wrapper, print-preview renderer and Reports workspace wiring;
* feature documentation indexed in docs/INDEX.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dashboard_endpoint_exposes_receipt_numbering_audit():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/receipt-numbering-continuity"' in src
    assert "ReceiptNumberingContinuityResponse" in src
    # whole-book scan over the live Payment ledger, single ordered pass (no N+1)
    assert "Payment.receipt_number.is_not(None)" in src
    assert "Payment.payment_datetime.asc()" in src
    # reuses the Batch 87 numeric-suffix series parser instead of duplicating it
    assert "_receipt_numeric_suffix(receipt_number)" in src
    # per-series reconciliation fields are emitted
    for field in ("gap_count", "expected_count", "actual_count"):
        assert field in src
    assert "CurrentUserDependency" in src


def test_dashboard_schemas_expose_receipt_numbering_fields():
    src = _read("backend/app/schemas/dashboard.py")
    assert "class ReceiptSeriesGap" in src
    assert "class ReceiptNumberingContinuityResponse" in src
    for field in (
        "prefix",
        "first_number",
        "last_number",
        "expected_count",
        "actual_count",
        "gap_count",
        "missing_numbers",
        "duplicate_numbers",
        "as_of",
        "receipts_checked",
        "series_count",
        "clean_series_count",
        "total_gap_count",
    ):
        assert field in src
    assert '"ReceiptNumberingContinuityResponse"' in src or "ReceiptNumberingContinuityResponse," in src.split("__all__")[-1]


def test_api_wrapper_requests_receipt_numbering_feed():
    src = _read("frontend/js/api.js")
    assert "export async function getDashboardReceiptNumberingContinuity" in src
    assert "/api/v1/dashboard/receipt-numbering-continuity" in src


def test_print_renderer_surfaces_series_gaps_and_duplicates():
    src = _read("frontend/js/print.js")
    assert "createReceiptNumberingContinuityPrintPreview" in src
    assert "Receipt Series Summary" in src
    assert "Missing Numbers Detail" in src
    assert "Duplicate Receipt Numbers" in src
    assert "No numbering gaps detected." in src


def test_reports_workspace_wires_receipt_numbering_card():
    api = _read("frontend/js/api.js")
    print_src = _read("frontend/js/print.js")
    src = _read("frontend/js/reports.js")
    # end-to-end wiring: workspace card -> API wrapper -> print renderer
    assert "getDashboardReceiptNumberingContinuity" in api
    assert "createReceiptNumberingContinuityPrintPreview" in print_src
    assert "getDashboardReceiptNumberingContinuity" in src
    assert "createReceiptNumberingContinuityPrintPreview" in src
    assert "Receipt numbering continuity" in src
    assert 'id="receipt-numbering-limit"' in src
    assert 'id="receipt-numbering-prepare"' in src


def test_receipt_numbering_documented_and_indexed():
    doc = _read("docs/CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md")
    assert "Receipt Numbering Continuity Audit" in doc
    index = _read("docs/INDEX.md")
    assert "CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md" in index
