"""Batch 91 contract tests — Receivables Aging Print Envelope.

These tests lock the reporting/printing integration for the receivables
aging ledger rolled out in Batch 86:

* The aging bucketing is extracted into one shared derivation
  (``build_receivables_aging_result``) used by *both* the dashboard feed
  and the print envelope, so printed ledgers can never drift from screen.
* ``POST /reports/receivables-aging-print-envelope`` reuses the Batch 82
  live-payment outstanding scan (single grouped Payment pass, stored
  counters never trusted, Batch 68 clamp invariant).
* Print schemas expose stable bucket lines (always present even when
  empty) and per-invoice aging lines with envelope headline aggregates.
* Frontend: api wrapper, envelope-aware aging renderer, and the Reports
  workspace card now prepares the packet through the print envelope.
* Documentation exists and is indexed in docs/INDEX.md.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_shared_aging_derivation_extracted_in_dashboard_module():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # one implementation of the bucketing, exported for the reporting service
    assert "def build_receivables_aging_result(" in src
    assert '"build_receivables_aging_result"' in src.split("__all__")[-1]
    # the dashboard endpoint delegates to it instead of bucketing inline
    dash = src[src.index('"/receivables-aging"'):]
    assert "**build_receivables_aging_result(invoices, patients, paid_by_invoice, as_of)" in dash
    # standard buckets live in exactly one constant
    assert src.count('_RECEIVABLES_BUCKETS = (') == 1
    # Batch 91 docstring entry records the extraction
    assert "Batch 91" in src[:src.index("from __future__")]


def test_print_envelope_endpoint_and_service_share_the_derivation():
    ep = _read("backend/app/api/v1/endpoints/reporting.py")
    assert '"/receivables-aging-print-envelope"' in ep
    assert "ReceivablesAgingPrintEnvelope" in ep
    svc = _read("backend/app/services/reporting.py")
    assert "async def build_receivables_aging_print_envelope(" in svc
    # reuses the dashboard's shared helpers — no second aging implementation
    assert "from app.api.v1.endpoints.dashboard import build_receivables_aging_result" in svc
    assert "billing_service.list_outstanding_invoices" in svc
    # live-payment derivation identical to the Batch 82/86 feeds
    aging_src = svc[svc.index("def build_receivables_aging_print_envelope"):]
    aging_src = aging_src[:aging_src.index("async def", 10)] if "async def" in aging_src[10:] else aging_src
    assert "func.coalesce(func.sum(Payment.amount_paid), 0)" in aging_src
    assert "group_by(Payment.invoice_id)" in aging_src


def test_reporting_schemas_expose_aging_print_envelope():
    src = _read("backend/app/schemas/reporting.py")
    assert "class ReceivablesAgingPrintRequest(BaseSchema):" in src
    assert "limit: int = Field(default=200, ge=1, le=500)" in src
    for cls in (
        "ReceivablesAgingBucketPrintLine",
        "ReceivablesAgingInvoicePrintLine",
        "ReceivablesAgingPrintData",
        "ReceivablesAgingPrintEnvelope",
    ):
        assert f"class {cls}(BaseSchema):" in src
    # stable printed shape: every bucket carries its bounds and totals
    for field in ("label", "lower_days", "upper_days", "invoice_count", "total_outstanding"):
        assert field in src
    for field in (
        "invoice_number",
        "days_outstanding",
        "bucket_label",
        "amount_paid",
        "balance_due",
    ):
        assert field in src
    assert 'report_type: Literal["receivables_aging_print"]' in src
    exports = src.split("__all__")[-1]
    for name in (
        "ReceivablesAgingPrintRequest",
        "ReceivablesAgingBucketPrintLine",
        "ReceivablesAgingInvoicePrintLine",
        "ReceivablesAgingPrintData",
        "ReceivablesAgingPrintEnvelope",
    ):
        assert name in exports


def test_api_wrapper_posts_aging_print_envelope():
    api = _read("frontend/js/api.js")
    assert "buildReceivablesAgingPrintEnvelope" in api
    assert "/api/v1/reports/receivables-aging-print-envelope" in api
    assert 'method:"POST"' in api[api.index("buildReceivablesAgingPrintEnvelope"):][:200]


def test_print_renderer_accepts_envelope_with_dashboard_fallback():
    prn = _read("frontend/js/print.js")
    fn = prn[prn.index("export function createReceivablesAgingPrintPreview"):]
    fn = fn[:fn.index("\nexport function", 10)] if "\nexport function" in fn[10:] else fn
    # envelope-first with backward-compatible dashboard-payload fallback
    assert "{envelope=null,data=null" in fn
    assert "const src=envelope?.data??data??{};" in fn
    assert "envelope?.title||title" in fn
    # all rendered aggregates read from src, never the raw data arg
    assert "src?.invoice_count" in fn
    assert "src?.total_outstanding" in fn
    assert "money(src?.total_outstanding)" in fn
    # sections keep the stable printed shape
    assert "Aging Buckets" in fn
    assert "Aging Ledger" in fn
    assert "it.bucket_label" in fn


def test_reports_workspace_prepares_aging_through_envelope():
    rep = _read("frontend/js/reports.js")
    assert "buildReceivablesAgingPrintEnvelope" in rep
    # the card now goes through the print envelope, not the dashboard feed
    assert "getDashboardReceivablesAging" not in rep
    handler = rep[rep.index('#aging-prepare'):]
    handler = handler[:handler.index("\n")]
    assert "buildReceivablesAgingPrintEnvelope({limit,title:\"Receivables Aging Ledger\"})" in handler
    assert "createReceivablesAgingPrintPreview($(\"#print-preview-host\",box),{envelope:env})" in handler
    # status line reports envelope headline aggregates
    assert "${d.invoice_count} outstanding invoice(s), total ${d.total_outstanding}" in handler
    # ids render as plain attributes (no escaped-quote regression, Batch 89 lesson)
    assert 'id=\\"aging-limit\\"' in rep  # single-escaped convention inside template literal
    assert 'id=\\"aging-prepare\\"' in rep
    assert 'id=\\"aging-note\\"' in rep


def test_batch91_documentation_exists_and_indexed():
    doc = _read("docs/CLIENT_RECEIVABLES_AGING_PRINT_ENVELOPE.md")
    assert "Batch 91" in doc
    assert "/reports/receivables-aging-print-envelope" in doc
    assert "build_receivables_aging_result" in doc
    index = _read("docs/INDEX.md")
    assert "CLIENT_RECEIVABLES_AGING_PRINT_ENVELOPE.md" in index
