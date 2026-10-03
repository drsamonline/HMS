"""Batch 89 — Invoice Payment Reconciliation Ledger contracts.

Where Batch 82/86 only surfaced *outstanding* invoices, this ledger reconciles
**every** scanned invoice against the live ``Payment`` table: payments are
summed in a single grouped pass (no N+1; stored counters and status columns
are never trusted), ``amount_paid`` is clamped to the invoice total and
``balance_due`` kept non-negative so the Batch 68 atomic-consistency invariant
``amount_paid + balance_due == total_amount`` holds on every printed row.

Each row also carries the derived payment status next to the stored one
(``is_reconciled`` flags drift) plus the per-invoice receipt count, so billing
staff can prove collection state line-by-line before printing. Headline
aggregates sum back to ``invoices_checked`` and the totals satisfy
``total_billed == total_paid + total_outstanding``.

Locked-in surfaces:

* ``InvoicePaymentReconciliationItem`` / ``InvoicePaymentReconciliationResponse``
  schemas with the clamp/drift/receipt fields and headline aggregates;
* ``GET /dashboard/invoice-payment-reconciliation`` scanning live invoices and
  payments in bounded, N+1-free passes with the ``_derive_payment_status``
  taxonomy (unpaid / partial / paid);
* frontend API wrapper, print-preview renderer and Reports workspace wiring;
* feature documentation indexed in docs/INDEX.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dashboard_endpoint_exposes_reconciliation_ledger():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/invoice-payment-reconciliation"' in src
    assert "InvoicePaymentReconciliationResponse" in src
    # scans every non-cancelled invoice (most recent first), not just outstanding ones
    assert 'Invoice.payment_status != "cancelled"' in src
    assert "Invoice.invoice_date.desc()" in src
    # bounded scan: limit query param (default 200, hard max 500) applied once
    assert 'Query(default=200, ge=1, le=500)' in src
    assert ".limit(limit)" in src
    # single grouped pass over the live Payment ledger for all scanned invoices
    # (no N+1): stored counters/status are never trusted
    assert "Payment.invoice_id.in_(invoice_ids)" in src
    assert "Payment.amount_paid" in src
    # Batch 68 parity clamping keeps the per-row invariant intact
    assert "min(" in src
    assert "max(invoice.total_amount - amount_paid, Decimal(\"0\"))" in src
    # derived-vs-stored status drift and receipt counts emitted per row
    for field in ("stored_payment_status", "derived_payment_status", "receipt_count", "is_reconciled"):
        assert field in src
    assert "CurrentUserDependency" in src


def test_payment_status_derivation_taxonomy():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    # dedicated helper mirrors the Batch 68 unpaid/partial/paid derivation
    assert "def _derive_payment_status(total_amount: Decimal, amount_paid: Decimal) -> str:" in src
    helper = src.split("def _derive_payment_status")[1].split("@router")[0]
    assert 'return "unpaid"' in helper
    assert 'return "partial"' in helper
    assert 'return "paid"' in helper
    # boundary semantics: zero paid -> unpaid, paid >= total -> paid
    assert "amount_paid <= 0" in helper
    assert "amount_paid >= total_amount" in helper


def test_dashboard_schemas_expose_reconciliation_fields():
    src = _read("backend/app/schemas/dashboard.py")
    assert "class InvoicePaymentReconciliationItem" in src
    assert "class InvoicePaymentReconciliationResponse" in src
    for field in (
        "invoice_number",
        "invoice_date",
        "total_amount",
        "amount_paid",
        "balance_due",
        "stored_payment_status",
        "derived_payment_status",
        "receipt_count",
        "is_reconciled",
    ):
        assert field in src
    for field in (
        "as_of",
        "invoices_checked",
        "paid_invoices",
        "partially_paid_invoices",
        "unpaid_invoices",
        "total_billed",
        "total_paid",
        "total_outstanding",
        "items",
    ):
        assert field in src
    exports = src.split("__all__")[-1]
    assert '"InvoicePaymentReconciliationItem"' in exports
    assert '"InvoicePaymentReconciliationResponse"' in exports


def test_api_wrapper_requests_reconciliation_feed():
    src = _read("frontend/js/api.js")
    assert "export async function getDashboardInvoicePaymentReconciliation" in src
    assert "/api/v1/dashboard/invoice-payment-reconciliation" in src
    # limit forwarded as a query parameter with the backend default mirrored
    assert "options.limit??200" in src


def test_print_renderer_surfaces_summary_ledger_and_drift():
    src = _read("frontend/js/print.js")
    assert "createInvoicePaymentReconciliationPrintPreview" in src
    assert "Reconciliation Summary" in src
    assert "Reconciliation Ledger" in src
    assert "Status Drift Detail" in src
    # headline aggregate rows reconcile line-by-line on paper
    for label in (
        "Invoices checked",
        "Paid invoices",
        "Partially paid invoices",
        "Unpaid invoices",
        "Total billed",
        "Total paid",
        "Total outstanding",
    ):
        assert label in src
    # clean fallback when nothing drifted
    assert "No status drift detected" in src
    assert "it.is_reconciled===false" in src


def test_reports_workspace_wires_reconciliation_card():
    api = _read("frontend/js/api.js")
    print_src = _read("frontend/js/print.js")
    src = _read("frontend/js/reports.js")
    # end-to-end wiring: workspace card -> API wrapper -> print renderer
    assert "getDashboardInvoicePaymentReconciliation" in api
    assert "createInvoicePaymentReconciliationPrintPreview" in print_src
    assert "getDashboardInvoicePaymentReconciliation" in src
    assert "createInvoicePaymentReconciliationPrintPreview" in src
    assert "Invoice payment reconciliation ledger" in src
    # the card's input/button/note ids are wired end-to-end; inside the
    # template literal they must be plain `id="..."` (escaped variants render
    # invalid attributes and silently break the $("#...") lookups below)
    assert 'id="reconciliation-limit"' in src
    assert 'id="reconciliation-prepare"' in src
    assert 'id="reconciliation-note"' in src
    assert '"#reconciliation-limit"' in src
    assert '"#reconciliation-prepare"' in src


def test_reconciliation_documented_and_indexed():
    doc = _read("docs/CLIENT_INVOICE_PAYMENT_RECONCILIATION_LEDGER.md")
    assert "Invoice Payment Reconciliation Ledger" in doc
    index = _read("docs/INDEX.md")
    assert "CLIENT_INVOICE_PAYMENT_RECONCILIATION_LEDGER.md" in index
