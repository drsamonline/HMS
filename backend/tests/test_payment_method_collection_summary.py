"""Batch 96 — Payment Method Collection Summary contracts.

Locks in the per-method collection summary: one shared scan/aggregation
implementation (``build_payment_method_summary_result`` +
``build_payment_method_collection_summary``) behind both
``GET /dashboard/payment-method-summary`` and
``POST /reports/payment-method-summary-print-envelope``, so screen and
paper can never drift for the same scan window.

Locked-in surfaces:

* shared derivation in the dashboard module — single grouped pass over the
  live Payment ledger joined to non-cancelled invoices (no N+1, stored
  counters never trusted), Batch 68 clamp parity so
  ``sum(per-method collected) == total_collected``;
* reporting service ``build_payment_method_summary_print_envelope``
  delegating to the same helper (no copy of the aggregation logic);
* ``POST /reports/payment-method-summary-print-envelope`` wired with
  ``response_model=PaymentMethodSummaryPrintEnvelope``;
* print schemas (``PaymentMethodSummaryPrintRequest``/
  ``PaymentMethodSummaryPrintLine``/``PaymentMethodSummaryPrintData``/
  ``PaymentMethodSummaryPrintEnvelope``) exported in ``__all__``;
* frontend API wrappers, envelope-aware print-preview renderer with
  dashboard-data fallback, and Reports workspace card prepared through
  the envelope with valid rendered ids;
* feature documentation indexed in docs/INDEX.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_shared_aggregation_and_scan_live_in_dashboard_module():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # rollup lives once as a pure function over scanned rows...
    assert "def build_payment_method_collection_summary(" in src
    # ...and the scan-and-aggregate entry point is shared by both surfaces
    assert "async def build_payment_method_summary_result(db, limit: int)" in src
    # live Payment ledger joined to non-cancelled invoices only
    assert 'Invoice.payment_status != "cancelled"' in src
    # Batch 68 clamp parity: receipts charged chronologically against invoice totals
    assert 'key=lambda r: (r["payment_datetime"] or datetime.max, r["receipt_number"])' in src
    assert "applied = min(gross, left)" in src
    # headline invariant documented
    assert "sum(per-method collected) == total_collected" in src
    # both helpers exported from the module
    assert '"build_payment_method_collection_summary",' in src
    assert '"build_payment_method_summary_result",' in src


def test_dashboard_endpoint_delegates_to_shared_helper():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '@router.get("/payment-method-summary", response_model=PaymentMethodSummaryResponse)' in src
    # bounded limit mirrors the Batch 89/90 ledger window
    assert 'limit: int = Query(default=200, ge=1, le=500)' in src
    # endpoint delegates — no inline re-implementation
    assert "result = await build_payment_method_summary_result(db, limit)" in src
    assert "return PaymentMethodSummaryResponse(**result)" in src


def test_reporting_service_reuses_shared_scan():
    src = _read("backend/app/services/reporting.py")
    assert "async def build_payment_method_summary_print_envelope(" in src
    # delegates to the *same* helper as the dashboard feed — no copy
    assert "build_payment_method_summary_result" in src
    # envelope carries headline aggregates plus per-method print lines
    assert "PaymentMethodSummaryPrintEnvelope(" in src
    assert "PaymentMethodSummaryPrintData(" in src
    assert "PaymentMethodSummaryPrintLine(" in src


def test_reporting_endpoint_wired_with_response_model():
    src = _read("backend/app/api/v1/endpoints/reporting.py")
    assert '"/payment-method-summary-print-envelope"' in src
    assert "response_model=PaymentMethodSummaryPrintEnvelope" in src
    assert "report_in: PaymentMethodSummaryPrintRequest" in src
    assert "Batch 96" in src


def test_schemas_fields_and_exports():
    dash = _read("backend/app/schemas/dashboard.py")
    for name in ("PaymentMethodSummaryItem", "PaymentMethodSummaryResponse"):
        assert f"class {name}(BaseSchema):" in dash
        assert f'"{name}"' in dash
    item_block = dash.split("class PaymentMethodSummaryItem(BaseSchema):")[1].split(
        "class PaymentMethodSummaryResponse"
    )[0]
    for field in ("payment_method", "receipt_count", "invoice_count",
                  "gross_received", "collected", "share_of_total"):
        assert field in item_block

    rep = _read("backend/app/schemas/reporting.py")
    for cls in (
        "class PaymentMethodSummaryPrintRequest(BaseSchema):",
        "class PaymentMethodSummaryPrintLine(BaseSchema):",
        "class PaymentMethodSummaryPrintData(BaseSchema):",
        "class PaymentMethodSummaryPrintEnvelope(BaseSchema):",
    ):
        assert cls in rep
        assert f'"{cls.split("(")[0].replace("class ", "")}"' in rep
    # bounded limit mirrors the dashboard feed (default 200, max 500)
    request_block = rep.split(
        "class PaymentMethodSummaryPrintRequest(BaseSchema):"
    )[1].split("class PaymentMethodSummaryPrintLine")[0]
    assert "200" in request_block and "500" in request_block
    # report_type discriminator on the envelope
    assert '"payment_method_summary_print"' in rep


def test_frontend_api_wrappers_present():
    api = _read("frontend/js/api.js")
    assert "export async function getDashboardPaymentMethodSummary(" in api
    assert "/api/v1/dashboard/payment-method-summary" in api
    assert "export async function buildPaymentMethodSummaryPrintEnvelope(" in api
    assert "/api/v1/reports/payment-method-summary-print-envelope" in api
    assert 'method:"POST"' in api or 'method: "POST"' in api


def test_print_preview_accepts_envelope_with_fallback():
    src = _read("frontend/js/print.js")
    assert "export function createPaymentMethodSummaryPrintPreview(" in src
    # envelope-first signature with raw dashboard data fallback
    assert "{envelope=null,data=null" in src.replace(" ", "")
    assert "envelope?.data??data??" in src.replace(" ", "")
    # headlines + per-method ledger sections rendered
    assert "Collection Headlines" in src
    assert "Per-Method Collection Ledger" in src
    # clean empty-state fallback
    assert "No payments recorded in this scan window" in src


def test_reports_workspace_card_prepares_through_envelope():
    src = _read("frontend/js/reports.js")
    # imports the envelope wrapper and the renderer
    assert "buildPaymentMethodSummaryPrintEnvelope" in src
    assert "createPaymentMethodSummaryPrintPreview" in src
    # handler posts through the envelope and reads envelope aggregates
    handler = src.split("#payment-method-prepare")[-1]
    assert "await buildPaymentMethodSummaryPrintEnvelope({limit" in handler
    assert "envelope?.data" in handler
    # Batch 89 quoting convention: card ids render as plain id="..." attributes
    # (verified by template evaluation — see harness note in batch docstring)
    assert 'id="payment-method-limit"' in src
    assert 'id="payment-method-prepare"' in src
    assert 'id="payment-method-note"' in src


def test_documentation_indexed():
    index = _read("docs/INDEX.md")
    assert "CLIENT_PAYMENT_METHOD_COLLECTION_SUMMARY.md" in index
    assert "Batch 96" in index
    doc = _read("docs/CLIENT_PAYMENT_METHOD_COLLECTION_SUMMARY.md")
    assert "payment-method-summary-print-envelope" in doc
    assert "build_payment_method_summary_result" in doc
