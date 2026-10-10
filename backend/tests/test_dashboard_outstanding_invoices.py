"""Batch 82 — Outstanding Billing Continuity contracts.

Locks in the surfaces that turn the billing service's oldest-first
outstanding-invoice feed into an actionable dashboard receivables panel:

* ``BillingService.list_outstanding_invoices`` derives balances from live
  payments (never a stale stored status) and excludes paid/cancelled rows,
* a dedicated /dashboard/outstanding-invoices endpoint with patient
  enrichment and per-row balance reconciliation,
* response schemas exposing the actionable receivable fields,
* frontend API wrapper and dashboard rendering wired to the patient workspace.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_billing_service_exposes_outstanding_feed():
    src = _read("backend/app/services/billing.py")
    assert "async def list_outstanding_invoices" in src
    # unpaid/partial candidates only; cancelled/paid never surface
    assert 'Invoice.payment_status.in_(("unpaid", "partial"))' in src
    # balance derived from live payments, not the stored status alone
    assert "func.coalesce(func.sum(Payment.amount_paid), 0)" in src
    assert "total_balance" in src
    # oldest-first ordering for chase-up priority
    assert "Invoice.invoice_date.asc()" in src


def test_dashboard_endpoint_module_wired_to_billing_service():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert 'prefix="/dashboard"' in src
    assert '"/outstanding-invoices"' in src
    assert "billing_service.list_outstanding_invoices" in src
    # enrichment so receivables are actionable, not bare IDs
    assert "patient_name" in src
    assert "days_outstanding" in src
    assert "balance_due" in src
    assert "CurrentUserDependency" in src


def test_dashboard_router_registered_on_api():
    src = _read("backend/app/api/v1/api.py")
    assert "from app.api.v1.endpoints.dashboard import router as dashboard_router" in src
    assert "include_router(dashboard_router)" in src


def test_dashboard_schemas_expose_receivable_fields():
    src = _read("backend/app/schemas/dashboard.py")
    for field in (
        "invoice_id",
        "patient_id",
        "patient_name",
        "invoice_number",
        "total_amount",
        "amount_paid",
        "balance_due",
        "payment_status",
        "days_outstanding",
    ):
        assert field in src
    assert "class OutstandingInvoicesResponse" in src
    assert "total_outstanding" in src
    assert "invoice_count" in src


def test_frontend_wrapper_and_dashboard_rendering():
    api = _read("frontend/js/api.js")
    dash = _read("frontend/js/dashboard.js")
    assert "/api/v1/dashboard/outstanding-invoices" in api
    assert "getDashboardOutstandingInvoices" in api
    assert "getDashboardOutstandingInvoices" in dash
    assert "dashboard-outstanding-invoices" in dash
    assert "Outstanding invoices" in dash
