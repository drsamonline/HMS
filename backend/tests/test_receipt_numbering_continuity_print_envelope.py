"""Batch 93 — Receipt Numbering Continuity Print Envelope contracts.

Locks in the screen/paper parity extraction: the Batch 88 whole-book
numbering audit moved out of the dashboard endpoint body into the shared
``build_receipt_numbering_continuity_result`` derivation, which both
``GET /dashboard/receipt-numbering-continuity`` and the new reporting print
envelope endpoint run through, so printed per-series figures can never
drift from the screen feed for the same scan window.

Locked-in surfaces:

* shared derivation ``build_receipt_numbering_continuity_result`` in the
  dashboard module (single ordered Payment pass, no N+1, shared
  ``_receipt_numeric_suffix`` parsing) with the per-series reconciliation
  invariant ``expected_count == actual_count + gap_count``;
* ``POST /reports/receipt-numbering-continuity-print-envelope`` delegating
  to that same helper via the reporting service;
* print schemas (``ReceiptNumberingContinuityPrintRequest``/
  ``ReceiptSeriesPrintLine``/``ReceiptNumberingContinuityPrintData``/
  ``ReceiptNumberingContinuityPrintEnvelope``) exported in ``__all__``;
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
    # the audit body now lives in one shared async helper...
    assert "async def build_receipt_numbering_continuity_result(db, limit: int) -> dict:" in src
    # ...and the dashboard endpoint delegates to it instead of re-implementing
    assert "audit = await build_receipt_numbering_continuity_result(db, limit)" in src
    assert "ReceiptNumberingContinuityResponse(**audit)" in src
    # single ordered pass over the live Payment ledger (no N+1)
    assert "Payment.receipt_number.is_not(None)" in src
    assert "Payment.payment_datetime.asc()" in src
    # reuses the Batch 87 numeric-suffix series parser
    assert "_receipt_numeric_suffix(receipt_number)" in src
    # per-series reconciliation fields are emitted by the shared derivation
    for field in ("gap_count", "expected_count", "actual_count"):
        assert f'"{field}"' in src
    # Batch 93 documented in the module docstring
    assert "Batch 93" in src


def test_reporting_service_reuses_shared_scan():
    src = _read("backend/app/services/reporting.py")
    assert (
        "async def build_receipt_numbering_continuity_print_envelope(" in src
    )
    # delegates to the *same* derivation as the dashboard feed — no copy
    assert "build_receipt_numbering_continuity_result" in src
    assert "from app.api.v1.endpoints.dashboard import" in src
    # envelope carries the printable packet metadata plus the audit payload
    assert "ReceiptNumberingContinuityPrintEnvelope(" in src
    assert "ReceiptNumberingContinuityPrintData(" in src
    assert "ReceiptSeriesPrintLine(**item)" in src


def test_reporting_endpoint_exposes_numbering_print_envelope():
    src = _read("backend/app/api/v1/endpoints/reporting.py")
    assert '"/receipt-numbering-continuity-print-envelope"' in src
    assert "response_model=ReceiptNumberingContinuityPrintEnvelope" in src
    assert "ReceiptNumberingContinuityPrintRequest" in src
    assert (
        "reporting_service.build_receipt_numbering_continuity_print_envelope" in src
    )


def test_reporting_schemas_expose_numbering_print_fields_and_exports():
    src = _read("backend/app/schemas/reporting.py")
    for cls in (
        "class ReceiptNumberingContinuityPrintRequest(BaseSchema)",
        "class ReceiptSeriesPrintLine(BaseSchema)",
        "class ReceiptNumberingContinuityPrintData(BaseSchema)",
        "class ReceiptNumberingContinuityPrintEnvelope(BaseSchema)",
    ):
        assert cls in src
    # bounded scan window mirrors the dashboard feed default (2000 receipts)
    assert "default=2000" in src
    # discriminator literal keeps print packets machine-checkable
    assert '"receipt_numbering_continuity_print"' in src
    # per-series reconciliation fields present on the printed line schema
    for field in ("prefix", "first_number", "last_number", "expected_count",
                  "actual_count", "gap_count", "missing_numbers",
                  "duplicate_numbers"):
        assert field in src
    # all four schemas exported
    exports = src.split("__all__")[1]
    for name in (
        "ReceiptNumberingContinuityPrintRequest",
        "ReceiptSeriesPrintLine",
        "ReceiptNumberingContinuityPrintData",
        "ReceiptNumberingContinuityPrintEnvelope",
    ):
        assert f'"{name}"' in exports


def test_client_api_exposes_numbering_print_envelope_wrapper():
    api_src = _read("frontend/js/api.js")
    assert "export async function buildReceiptNumberingContinuityPrintEnvelope" in api_src
    assert "/api/v1/reports/receipt-numbering-continuity-print-envelope" in api_src
    assert 'method:"POST"' in api_src


def test_print_preview_accepts_envelope_with_dashboard_fallback():
    src = _read("frontend/js/print.js")
    assert "export function createReceiptNumberingContinuityPrintPreview" in src
    # signature accepts both {envelope} (print path) and {data} (feed path)
    assert "{envelope=null,data=null" in src
    # envelope-first payload resolution keeps older callers working
    assert "envelope?.data??data??" in src
    # title flows from the envelope when provided, falling back to arg
    assert "envelope?.title||title" in src
    # printed sections cover summary / series / missing / duplicates
    for marker in ("Audit Summary", "Receipt Series Summary",
                   "Missing Numbers Detail", "Duplicate Receipt Numbers"):
        assert marker in src


def test_reports_workspace_numbering_card_prepares_through_envelope():
    src = _read("frontend/js/reports.js")
    # card handler posts through the print envelope instead of the raw feed
    assert 'buildReceiptNumberingContinuityPrintEnvelope({limit' in src
    assert "createReceiptNumberingContinuityPrintPreview" in src
    assert "{envelope:env}" in src
    # status line reads aggregates off the envelope payload
    assert "receipts_checked" in src and "series_count" in src
    # Batch 89 single-escaped id convention preserved: ids render as valid
    # id="..." attributes inside the template literal (never double-escaped)
    assert 'id=\\\\"' not in src
    assert 'id=\\"receipt-numbering-limit\\"' in src
    assert 'id=\\"receipt-numbering-prepare\\"' in src


def test_numbering_print_envelope_docs_indexed():
    index = _read("docs/INDEX.md")
    assert "CLIENT_RECEIPT_NUMBERING_CONTINUITY_PRINT_ENVELOPE.md" in index
    doc = ROOT / "docs" / "CLIENT_RECEIPT_NUMBERING_CONTINUITY_PRINT_ENVELOPE.md"
    assert doc.exists()
    body = doc.read_text(encoding="utf-8")
    assert "/reports/receipt-numbering-continuity-print-envelope" in body
    assert "build_receipt_numbering_continuity_result" in body
