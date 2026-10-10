"""Batch 95 — Collection Summary Print Envelope contracts.

Locks in the screen/paper parity switch: the Reports workspace "Collection
summary by patient" card now prepares through
``POST /reports/collection-summary-print-envelope``, which delegates to the
exact same shared scan/aggregation pair that backs
``GET /dashboard/collection-summary-by-patient`` (``_build_reconciliation_rows``
+ ``build_collection_summary_by_patient``), so printed collection lines can
never drift from the screen feed for the same scan window.

Locked-in surfaces:

* shared derivation in the dashboard module — single grouped Payment pass,
  no N+1, stored counters never trusted, Batch 68 clamp invariant;
* reporting service ``build_collection_summary_print_envelope`` reusing both
  helpers (no copy of the scan/aggregation logic);
* ``POST /reports/collection-summary-print-envelope`` wired with
  ``response_model=CollectionSummaryPrintEnvelope``;
* print schemas (``CollectionSummaryPrintRequest``/
  ``PatientCollectionSummaryPrintLine``/``CollectionSummaryPrintData``/
  ``CollectionSummaryPrintEnvelope``) exported in ``__all__``;
* frontend API wrapper, envelope-aware print-preview renderer with
  dashboard-data fallback, and Reports workspace card switched to the
  envelope;
* feature documentation indexed in docs/INDEX.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_shared_scan_and_aggregation_remain_in_dashboard_module():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # the row scan and the per-patient rollup live once, in the dashboard module
    assert "async def _build_reconciliation_rows(db, limit: int)" in src
    assert "def build_collection_summary_by_patient(rows: list[dict]) -> dict:" in src
    # single grouped pass over the Payment ledger (no N+1)
    assert "group_by(Payment.invoice_id)" in src
    # Batch 90 endpoint delegates to the same pair
    assert '@router.get(\n    "/collection-summary-by-patient"' in src
    # Batch 95 documented in the module docstring
    assert "Batch 95" in src


def test_reporting_service_reuses_shared_scan_and_aggregation():
    src = _read("backend/app/services/reporting.py")
    assert "async def build_collection_summary_print_envelope(" in src
    # delegates to the *same* helpers as the dashboard feed — no copy
    assert "_build_reconciliation_rows" in src
    assert "build_collection_summary_by_patient" in src
    # envelope carries headline aggregates plus per-patient print lines
    assert "CollectionSummaryPrintEnvelope(" in src
    assert "CollectionSummaryPrintData(" in src
    assert "PatientCollectionSummaryPrintLine(" in src


def test_reporting_endpoint_wired_with_response_model():
    src = _read("backend/app/api/v1/endpoints/reporting.py")
    assert '"/collection-summary-print-envelope"' in src
    assert "response_model=CollectionSummaryPrintEnvelope" in src
    assert "report_in: CollectionSummaryPrintRequest" in src
    # Batch 90 documented in the endpoint docstring
    assert "Batch 90" in src


def test_print_schemas_fields_and_exports():
    src = _read("backend/app/schemas/reporting.py")
    for cls in (
        "class CollectionSummaryPrintRequest(BaseSchema):",
        "class PatientCollectionSummaryPrintLine(BaseSchema):",
        "class CollectionSummaryPrintData(BaseSchema):",
        "class CollectionSummaryPrintEnvelope(BaseSchema):",
    ):
        assert cls in src
    # bounded limit mirrors the dashboard feed (default 200, max 500)
    request_block = src.split(
        "class CollectionSummaryPrintRequest(BaseSchema):"
    )[1].split("class PatientCollectionSummaryPrintLine")[0]
    assert "200" in request_block and "500" in request_block
    # report_type discriminator on the envelope
    assert '"collection_summary_print"' in src
    # all four exported in __all__
    for name in (
        "CollectionSummaryPrintRequest",
        "PatientCollectionSummaryPrintLine",
        "CollectionSummaryPrintData",
        "CollectionSummaryPrintEnvelope",
    ):
        assert f'"{name}"' in src


def test_frontend_api_wrapper_present():
    api = _read("frontend/js/api.js")
    assert "export async function buildCollectionSummaryPrintEnvelope(" in api
    assert "/api/v1/reports/collection-summary-print-envelope" in api
    assert 'method:"POST"' in api or 'method: "POST"' in api


def test_print_preview_accepts_envelope_with_fallback():
    src = _read("frontend/js/print.js")
    assert "export function createCollectionSummaryPrintPreview(" in src
    # envelope-first signature with raw dashboard data fallback
    assert "{envelope=null,data=null" in src.replace(" ", "")
    assert "envelope?.data??data??" in src.replace(" ", "")
    # headlines + per-patient ledger sections rendered
    assert "Collection Summary Headlines" in src
    assert "Per-Patient Collection Ledger" in src


def test_reports_workspace_card_prepares_through_envelope():
    src = _read("frontend/js/reports.js")
    # imports the envelope wrapper (not just the dashboard feed)
    assert "buildCollectionSummaryPrintEnvelope" in src
    assert "createCollectionSummaryPrintPreview" in src
    # the card no longer posts through the raw dashboard feed
    assert "getDashboardCollectionSummaryByPatient" not in src
    # handler posts through the envelope and reads envelope aggregates
    handler = src.split("#collection-summary-prepare")[-1]
    assert "await buildCollectionSummaryPrintEnvelope({limit" in handler
    assert "envelope?.data" in handler
    # Batch 89 quoting convention preserved: ids render as plain id="..."
    assert 'id=\\"collection-summary-limit\\"' in src
    assert 'id=\\"collection-summary-prepare\\"' in src


def test_documentation_indexed():
    index = _read("docs/INDEX.md")
    assert "CLIENT_COLLECTION_SUMMARY_PRINT_ENVELOPE.md" in index
    assert "Batch 95" in index
    doc = _read("docs/CLIENT_COLLECTION_SUMMARY_PRINT_ENVELOPE.md")
    assert "collection-summary-print-envelope" in doc
    assert "build_collection_summary_by_patient" in doc
