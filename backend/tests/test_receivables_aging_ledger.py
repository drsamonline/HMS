"""Batch 86 — Receivables Aging Ledger contracts.

Locks in the surfaces that turn the live outstanding-invoice feed into a
financial-style aging ledger ready for reporting/printing:

* GET /dashboard/receivables-aging built on the same Batch 82
  ``billing_service.list_outstanding_invoices`` derivation so balances always
  reconcile (live payments, clamped so ``total == paid + balance``),
* stable 0-30 / 31-60 / 61-90 / Over-90 buckets reported even when empty,
  with bucket counts/totals summing back to the headline aggregates,
* response schemas exposing per-bucket and per-invoice aging fields,
* frontend API wrapper plus aging print-preview rendering wired into the
  Reports & Printing workspace.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dashboard_endpoint_exposes_receivables_aging():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/receivables-aging"' in src
    assert "response_model=ReceivablesAgingResponse" in src
    # built on the Batch 82 live outstanding derivation, never stored status
    assert "billing_service.list_outstanding_invoices" in src
    assert "CurrentUserDependency" in src


def test_aging_buckets_are_standard_and_stable():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    for label in ("0-30 days", "31-60 days", "61-90 days", "Over 90 days"):
        assert label in src
    # every bucket is emitted even when empty so printed ledgers keep shape
    assert "_RECEIVABLES_BUCKETS" in src
    assert "bucket_stats[label][\"count\"]" in src


def test_aging_balances_use_live_payments_with_clamping():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # identical reconciliation semantics to Batch 82/85
    assert "func.coalesce(func.sum(Payment.amount_paid), 0)" in src
    assert "amount_paid = min(" in src
    assert "balance_due = max(invoice.total_amount - amount_paid, Decimal(\"0\"))" in src
    # age computed from invoice date to today, never negative
    assert "days_outstanding = max((as_of - invoice_local_date).days, 0)" in src
    # batched patient enrichment (no N+1)
    assert "Patient.id.in_(patient_ids)" in src


def test_aging_schemas_expose_bucket_and_item_fields():
    src = _read("backend/app/schemas/dashboard.py")
    for cls in (
        "class ReceivablesAgingBucket",
        "class ReceivablesAgingItem",
        "class ReceivablesAgingResponse",
    ):
        assert cls in src
    for field in (
        "label",
        "lower_days",
        "upper_days",
        "invoice_count",
        "total_outstanding",
        "days_outstanding",
        "bucket_label",
        "balance_due",
    ):
        assert field in src
    # exported so the endpoint can import them
    for name in ("ReceivablesAgingBucket", "ReceivablesAgingItem", "ReceivablesAgingResponse"):
        assert name in src.split("__all__")[-1]


def test_frontend_wrapper_calls_receivables_aging_endpoint():
    api = _read("frontend/js/api.js")
    assert "getDashboardReceivablesAging" in api
    assert "/api/v1/dashboard/receivables-aging" in api


def test_print_renderer_builds_aging_ledger_preview():
    prn = _read("frontend/js/print.js")
    assert "export function createReceivablesAgingPrintPreview" in prn
    assert "Aging Buckets" in prn
    assert "Aging Ledger" in prn
    # money formatting reused so totals print consistently
    assert "money(b.total_outstanding)" in prn
    assert "it.bucket_label" in prn


def test_reports_workspace_wires_aging_card():
    rep = _read("frontend/js/reports.js")
    # Batch 91 — the Reports workspace now prepares the aging ledger through
    # the print envelope endpoint (one shared derivation for screen + paper).
    assert "buildReceivablesAgingPrintEnvelope" in rep
    assert "createReceivablesAgingPrintPreview" in rep
    assert "aging-prepare" in rep
    assert "Receivables aging ledger" in rep


def test_batch86_documentation_exists_and_indexed():
    doc = _read("docs/CLIENT_RECEIVABLES_AGING_LEDGER.md")
    assert "Batch 86" in doc
    assert "/dashboard/receivables-aging" in doc
    index = _read("docs/INDEX.md")
    assert "CLIENT_RECEIVABLES_AGING_LEDGER.md" in index
