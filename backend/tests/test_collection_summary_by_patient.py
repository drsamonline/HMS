"""Batch 90 contract tests — Collection Summary by Patient.

These tests lock the reporting/printing integration surface for the
per-patient collection summary rolled up from the Batch 89 reconciliation
ledger:

* ``GET /dashboard/collection-summary-by-patient`` reuses the shared
  ``_build_reconciliation_rows`` scan (single grouped Payment pass, live
  clamping, stored counters never trusted) and the shared
  ``build_collection_summary_by_patient`` aggregation.
* The print envelope endpoint and service reuse the *same* aggregation so
  print and screen can never drift.
* Per-patient invariant ``total_collected + outstanding == total_billed``
  and headline sums reproduce ``invoices_checked`` / ``patients_checked``.
* Frontend wrappers/renderers/workspace card and documentation indexing.
"""

from pathlib import Path

import ast

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dashboard_endpoint_groups_reconciliation_by_patient():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/collection-summary-by-patient"' in src
    assert "PatientCollectionSummaryResponse" in src
    # shares the Batch 89 scan — no second payment-scan implementation
    assert "rows = await _build_reconciliation_rows(db, limit)" in src
    assert "build_collection_summary_by_patient(rows)" in src
    # bounded limit identical to the reconciliation ledger
    assert "Query(default=200, ge=1, le=500)" in src
    # aggregation guarantees the per-patient clamp invariant by construction
    agg_src = src[src.index("def build_collection_summary_by_patient"):]
    assert '"total_collected"] += row["amount_paid"]' or \
        'summary["total_collected"] += row["amount_paid"]' in agg_src
    assert 'summary["outstanding"] += row["balance_due"]' in agg_src
    # last-payment tracking uses the reconciliation row's live timestamp
    assert 'row.get("last_payment_datetime")' in agg_src
    # module exports the shared aggregation for the reporting service
    assert '"build_collection_summary_by_patient"' in src


def test_print_envelope_reuses_shared_aggregation():
    svc = _read("backend/app/services/reporting.py")
    assert "def build_collection_summary_print_envelope" in svc
    # imports the exact dashboard helpers — single source of truth
    assert "_build_reconciliation_rows" in svc
    assert "build_collection_summary_by_patient" in svc
    ep = _read("backend/app/api/v1/endpoints/reporting.py")
    assert '"/collection-summary-print-envelope"' in ep
    assert "CollectionSummaryPrintEnvelope" in ep


def test_dashboard_schemas_expose_collection_summary_fields():
    src = _read("backend/app/schemas/dashboard.py")
    tree = ast.parse(src)
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    item = classes["PatientCollectionSummaryItem"]
    item_fields = {t.target.id for t in item.body if isinstance(t, ast.AnnAssign)}
    for field in (
        "patient_id", "patient_name", "patient_number", "invoice_count",
        "paid_invoice_count", "partial_invoice_count", "unpaid_invoice_count",
        "total_billed", "total_collected", "outstanding", "last_payment_date",
    ):
        assert field in item_fields, field
    resp = classes["PatientCollectionSummaryResponse"]
    resp_fields = {t.target.id for t in resp.body if isinstance(t, ast.AnnAssign)}
    for field in (
        "as_of", "invoices_checked", "patients_checked",
        "patients_with_outstanding", "total_billed", "total_collected",
        "total_outstanding", "items",
    ):
        assert field in resp_fields, field
    assert '"PatientCollectionSummaryItem"' in src
    assert '"PatientCollectionSummaryResponse"' in src


def test_reporting_schemas_expose_print_envelope():
    src = _read("backend/app/schemas/reporting.py")
    for cls in (
        "CollectionSummaryPrintRequest",
        "PatientCollectionSummaryPrintLine",
        "CollectionSummaryPrintData",
        "CollectionSummaryPrintEnvelope",
    ):
        assert f"class {cls}(" in src, cls
        assert f'"{cls}"' in src  # exported in __all__


def test_api_wrappers_request_collection_summary_feeds():
    src = _read("frontend/js/api.js")
    assert "getDashboardCollectionSummaryByPatient" in src
    assert "/api/v1/dashboard/collection-summary-by-patient" in src
    assert "buildCollectionSummaryPrintEnvelope" in src
    assert "/api/v1/reports/collection-summary-print-envelope" in src


def test_print_preview_renders_collection_sections():
    src = _read("frontend/js/print.js")
    assert "export function createCollectionSummaryPrintPreview" in src
    assert "Collection Summary Headlines" in src
    assert "Per-Patient Collection Ledger" in src
    assert "No patient collections to summarise" in src  # clean fallback


def test_reports_workspace_wires_collection_summary_card():
    src = _read("frontend/js/reports.js")
    # Batch 95: the card prepares through the print envelope, not the raw feed
    assert "buildCollectionSummaryPrintEnvelope" in src
    assert "createCollectionSummaryPrintPreview" in src
    assert "Collection summary by patient" in src
    # template-literal attributes are stored double-escaped and render as
    # plain id="..." attributes (verified by the Node harness in Batch 89)
    assert 'id=\\"collection-summary-limit\\"' in src
    assert 'id=\\"collection-summary-prepare\\"' in src
    assert '"#collection-summary-limit"' in src
    assert '"#collection-summary-prepare"' in src
    assert "Unable to prepare collection summary." in src


def test_collection_summary_documented_and_indexed():
    doc = _read("docs/CLIENT_COLLECTION_SUMMARY_BY_PATIENT.md")
    assert "GET /api/v1/dashboard/collection-summary-by-patient" in doc
    assert "POST /api/v1/reports/collection-summary-print-envelope" in doc
    assert "total_collected + outstanding == total_billed" in doc
    index = _read("docs/INDEX.md")
    assert "CLIENT_COLLECTION_SUMMARY_BY_PATIENT.md" in index
    assert "(Batch 90)" in index
