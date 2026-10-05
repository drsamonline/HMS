"""Batch 100 — Settlement/Refund Audit Feeds & Operational Print Envelopes.

Locks in the payment-analysis continuity track and the reporting/printing
integration delivered as Batch 100:

* ``GET /dashboard/invoice-settlement-audit`` — every recent invoice split
  into settled/outstanding via the shared clamped reconciliation scan
  (Batch 68 clamp semantics reused verbatim), with cleared/unsettled
  headlines;
* ``GET /dashboard/refund-audit`` — negative ``Payment`` rows audited for
  processing drift (invoice link, remarks note, non-negative net
  collections) with processed/drifted headlines;
* four print envelopes reusing the exact same shared scans/derivations —
  ``POST /reports/invoice-settlement-audit-print-envelope``,
  ``POST /reports/refund-audit-print-envelope``,
  ``POST /reports/discharge-audit-print-envelope`` (Batch 99 hook),
  ``POST /reports/opd-queue-summary-print-envelope`` (Batch 99 hook);
* the Batch 97 ghost-card fix: the Invoice Overpayment Ledger surface is
  now reachable from the Reports & Printing workspace (card + handler +
  imports), closing the gap where server-side endpoints existed but no UI
  card wired them;
* frontend API wrappers, envelope-aware preview renderers and report
  cards for all five payment/operational surfaces;
* documentation indexed in ``docs/INDEX.md``.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Pure derivation: invoice settlement audit
# ---------------------------------------------------------------------------


def _settlement_row(**overrides):
    row = {
        "invoice_id": 1,
        "invoice_number": "INV-0001",
        "invoice_date": datetime(2026, 10, 4, 9, 0, 0),
        "patient_id": 11,
        "patient_name": "Ann Test",
        "patient_number": "P-0011",
        "total_amount": Decimal("500"),
        "amount_paid": Decimal("500"),
        "balance_due": Decimal("0"),
        "total_paid_raw": Decimal("500"),
        "stored_payment_status": "paid",
        "derived_payment_status": "paid",
        "receipt_count": 1,
        "refund_count": 0,
        "is_reconciled": True,
    }
    row.update(overrides)
    return row


def test_settlement_audit_result_splits_and_headlines():
    from app.api.v1.endpoints.dashboard import build_invoice_settlement_audit_result

    as_of = date(2026, 10, 5)
    rows = [
        _settlement_row(),  # fully cleared
        _settlement_row(
            invoice_id=2,
            amount_paid=Decimal("200"),
            balance_due=Decimal("300"),
            total_paid_raw=Decimal("200"),
            stored_payment_status="partial",
            derived_payment_status="partial",
        ),
        _settlement_row(
            invoice_id=3,
            total_amount=Decimal("100"),
            amount_paid=Decimal("0"),
            balance_due=Decimal("100"),
            total_paid_raw=Decimal("0"),
            stored_payment_status="unpaid",
            derived_payment_status="unpaid",
            receipt_count=0,
        ),
        _settlement_row(
            invoice_id=4,
            total_amount=Decimal("100"),
            amount_paid=Decimal("100"),
            balance_due=Decimal("0"),
            total_paid_raw=Decimal("150"),  # over-collected: clamp applies
        ),
    ]
    result = build_invoice_settlement_audit_result(rows, as_of)

    assert result["total_invoices"] == 4
    assert result["cleared_count"] + result["unsettled_count"] == result["total_invoices"]
    assert result["cleared_count"] == 2
    assert result["unsettled_count"] == 2

    by_id = {item["invoice_id"]: item for item in result["items"]}
    for item in result["items"]:
        assert (
            item["settled_amount"] + item["outstanding_amount"] == item["total_amount"]
        )
    assert by_id[2]["is_cleared"] is False
    assert by_id[2]["outstanding_amount"] == Decimal("300")
    # over-collection stays visible but never breaks the clamp invariant
    assert by_id[4]["is_cleared"] is True
    assert by_id[4]["overpayment_amount"] == Decimal("50")
    assert by_id[1]["overpayment_amount"] == Decimal("0")

    assert result["total_billed"] == Decimal("1200")
    assert result["total_collected"] == Decimal("900")
    assert result["total_outstanding"] == Decimal("300")
    assert (
        result["total_billed"]
        == result["total_collected"] + result["total_outstanding"]
    )


def test_settlement_audit_empty_scan_is_clean():
    from app.api.v1.endpoints.dashboard import build_invoice_settlement_audit_result

    result = build_invoice_settlement_audit_result([], date(2026, 10, 5))
    assert result["items"] == []
    assert result["total_invoices"] == 0
    assert result["cleared_count"] == 0
    assert result["unsettled_count"] == 0
    assert result["total_billed"] == Decimal("0")


# ---------------------------------------------------------------------------
# Pure derivation: refund processing audit
# ---------------------------------------------------------------------------


def _refund_row(**overrides):
    row = {
        "payment_id": 1,
        "receipt_number": "RCT-0001",
        "payment_datetime": datetime(2026, 10, 4, 12, 0, 0),
        "payment_method": "cash",
        "refund_amount": Decimal("50"),
        "invoice_id": 11,
        "invoice_number": "INV-0011",
        "invoice_total_amount": Decimal("500"),
        "invoice_net_paid": Decimal("450"),
        "received_by": 7,
        "remarks": "Duplicate payment adjusted",
    }
    row.update(overrides)
    return row


def test_refund_audit_flags_and_headline_split():
    from app.api.v1.endpoints.dashboard import build_refund_audit_result

    as_of = date(2026, 10, 5)
    rows = [
        _refund_row(),  # fully clean refund
        _refund_row(payment_id=2, remarks=None),  # missing explanation
        _refund_row(
            payment_id=3,
            invoice_id=None,
            invoice_number=None,
            invoice_total_amount=None,
            invoice_net_paid=None,
        ),  # orphaned refund
        _refund_row(
            payment_id=4,
            payment_datetime=datetime(2026, 10, 3, 12, 0, 0),
            invoice_net_paid=Decimal("-10"),
        ),  # net collections driven negative
    ]
    result = build_refund_audit_result(rows, as_of)

    assert result["total_refunds"] == 4
    assert result["processed_count"] + result["drifted_count"] == result["total_refunds"]
    assert result["processed_count"] == 1
    assert result["drifted_count"] == 3
    assert result["total_refunded"] == Decimal("200")

    items = result["items"]
    # newest refund first
    assert [item["payment_id"] for item in items] == [1, 2, 3, 4]

    by_id = {item["payment_id"]: item for item in items}
    assert by_id[1]["processing_complete"] is True
    assert by_id[2]["has_remarks"] is False
    assert by_id[2]["processing_complete"] is False
    assert by_id[3]["invoice_exists"] is False
    assert by_id[3]["net_non_negative"] is False
    assert by_id[3]["processing_complete"] is False
    assert by_id[4]["net_non_negative"] is False
    assert by_id[4]["processing_complete"] is False


def test_refund_audit_whitespace_remarks_do_not_count_as_documented():
    from app.api.v1.endpoints.dashboard import build_refund_audit_result

    result = build_refund_audit_result([_refund_row(remarks="   ")], date(2026, 10, 5))
    item = result["items"][0]
    assert item["has_remarks"] is False
    assert item["processing_complete"] is False


def test_refund_audit_empty_scan_is_clean():
    from app.api.v1.endpoints.dashboard import build_refund_audit_result

    result = build_refund_audit_result([], date(2026, 10, 5))
    assert result["items"] == []
    assert result["total_refunds"] == 0
    assert result["processed_count"] == 0
    assert result["drifted_count"] == 0
    assert result["total_refunded"] == Decimal("0")


# ---------------------------------------------------------------------------
# Pure derivations closing the Batch 97 / Batch 98 test gap
# ---------------------------------------------------------------------------


def _overpayment_row(**overrides):
    row = {
        "invoice_id": 1,
        "invoice_number": "INV-0001",
        "invoice_date": datetime(2026, 10, 4, 9, 0, 0),
        "patient_id": 11,
        "patient_name": "Ann Test",
        "patient_number": "P-0011",
        "total_amount": Decimal("500"),
        "total_paid_raw": Decimal("620"),
        "overpaid_amount": Decimal("120"),
        "receipt_count": 2,
        "stored_payment_status": "paid",
        "derived_payment_status": "paid",
    }
    row.update(overrides)
    return row


def test_overpayment_ledger_result_rollup_invariants():
    """Batch 97 shared rollup: overpaid == total_paid_raw - total_amount."""
    from app.api.v1.endpoints.dashboard import build_overpayment_ledger_result

    rows = [
        _overpayment_row(),
        _overpayment_row(
            invoice_id=2,
            total_amount=Decimal("100"),
            total_paid_raw=Decimal("130"),
            overpaid_amount=Decimal("30"),
        ),
    ]
    result = build_overpayment_ledger_result(rows, date(2026, 10, 5))

    assert result["invoices_checked"] == 2
    assert result["invoices_overpaid"] == len(result["items"]) == 2
    assert result["total_billed"] == Decimal("600")
    assert result["total_paid_raw"] == Decimal("750")
    assert result["total_overpaid"] == Decimal("150")
    # headline reconciles line-for-line with the per-row excess
    assert result["total_paid_raw"] - result["total_billed"] == result["total_overpaid"]
    for item in result["items"]:
        assert (
            item["overpaid_amount"] == item["total_paid_raw"] - item["total_amount"]
        )


def test_overpayment_ledger_result_empty_scan_is_clean():
    from app.api.v1.endpoints.dashboard import build_overpayment_ledger_result

    result = build_overpayment_ledger_result([], date(2026, 10, 5))
    assert result["items"] == []
    assert result["invoices_overpaid"] == 0
    assert result["total_overpaid"] == Decimal("0")


def _method_receipt(invoice_id, method, amount, when, receipt_number):
    return {
        "invoice_id": invoice_id,
        "receipt_number": receipt_number,
        "payment_method": method,
        "amount_paid": Decimal(str(amount)),
        "payment_datetime": when,
    }


def test_method_overpayment_breakdown_chronological_clamp():
    """Batch 98 shared breakdown: gross == collected + overpaid per method."""
    from app.api.v1.endpoints.dashboard import (
        build_payment_method_overpayment_breakdown,
    )

    day = datetime(2026, 10, 4, 10, 0, 0)
    receipts = [
        # invoice 1 billed 100: card pays 60 first, cash pays 80 -> 40 excess
        _method_receipt(1, "card", 60, day, "RCT-1"),
        _method_receipt(1, "cash", 80, day + timedelta(hours=1), "RCT-2"),
        # clean cash payment against invoice 2 (billed 50)
        _method_receipt(2, "cash", 50, day, "RCT-4"),
    ]
    invoice_totals = {1: Decimal("100"), 2: Decimal("50")}
    result = build_payment_method_overpayment_breakdown(receipts, invoice_totals, 2)

    by_method = {item["payment_method"]: item for item in result["items"]}
    assert by_method["card"]["collected"] == Decimal("60")
    assert by_method["card"]["overpaid"] == Decimal("0")
    # second receipt over-collects invoice 1 chronologically: 80 gross, 40 applied
    assert by_method["cash"]["gross_received"] == Decimal("130")
    assert by_method["cash"]["collected"] == Decimal("90")
    assert by_method["cash"]["overpaid"] == Decimal("40")
    for item in result["items"]:
        assert (
            item["gross_received"] == item["collected"] + item["overpaid"]
        )
    assert result["total_overpaid"] == Decimal("40")
    assert (
        result["total_gross"] == result["total_collected"] + result["total_overpaid"]
    )
    assert sum(item["overpaid"] for item in result["items"]) == result["total_overpaid"]


def test_method_overpayment_breakdown_out_of_window_receipts_do_not_inflate_split():
    """Receipts outside the scan window never touch the per-method split.

    The Batch 98 headline keeps ``total_gross == total_collected +
    total_overpaid`` by counting such receipts as neither collected nor
    overpaid; this locks that behaviour so a print envelope can never show
    phantom excess from invoices outside its window.
    """
    from app.api.v1.endpoints.dashboard import (
        build_payment_method_overpayment_breakdown,
    )

    day = datetime(2026, 10, 4, 10, 0, 0)
    receipts = [
        _method_receipt(1, "cash", 100, day, "RCT-1"),
        # invoice 99 sits outside the scanned window entirely
        _method_receipt(99, "upi", 500, day, "RCT-2"),
    ]
    result = build_payment_method_overpayment_breakdown(
        receipts, {1: Decimal("100")}, 1
    )
    by_method = {item["payment_method"]: item for item in result["items"]}
    assert by_method["upi"]["collected"] == Decimal("0")
    assert by_method["upi"]["overpaid"] == Decimal("0")
    assert result["total_collected"] == Decimal("100")
    assert result["total_overpaid"] == Decimal("0")
    assert (
        result["total_gross"] == result["total_collected"] + result["total_overpaid"]
    )


def test_method_overpayment_breakdown_empty_window_is_clean():
    from app.api.v1.endpoints.dashboard import (
        build_payment_method_overpayment_breakdown,
    )

    result = build_payment_method_overpayment_breakdown([], {}, 0)
    assert result["items"] == []
    assert result["total_overpaid"] == Decimal("0")
    assert result["invoices_checked"] == 0


# ---------------------------------------------------------------------------
# Endpoint wiring (dashboard feeds)
# ---------------------------------------------------------------------------


def test_settlement_audit_endpoint_wired_to_shared_scan():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/invoice-settlement-audit"' in src
    assert "response_model=InvoiceSettlementAuditResponse" in src
    assert "async def build_invoice_settlement_audit_scan" in src
    assert "build_invoice_settlement_audit_result(" in src
    # reuses the exact same grouped reconciliation row builder as Batch 89/94/97
    assert "await _build_reconciliation_rows(db, limit)" in src
    # single grouped refund-count pass, no per-row queries
    assert ".where(Payment.amount_paid < Decimal(\"0\"))" in src
    assert ".group_by(Payment.invoice_id)" in src
    assert 'limit: int = Query(default=200, ge=1, le=500)' in src


def test_refund_audit_endpoint_wired_to_shared_scan():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/refund-audit"' in src
    assert "response_model=RefundAuditResponse" in src
    assert "async def build_refund_audit_scan" in src
    assert "build_refund_audit_result(" in src
    # newest-first capped scan of negative ledger rows
    assert ".order_by(Payment.payment_datetime.desc(), Payment.id.desc())" in src


def test_batch100_helpers_exported_from_dashboard_module():
    import app.api.v1.endpoints.dashboard as dashboard_module

    for name in (
        "build_invoice_settlement_audit_result",
        "build_invoice_settlement_audit_scan",
        "build_refund_audit_result",
        "build_refund_audit_scan",
    ):
        assert name in dashboard_module.__all__
        assert callable(getattr(dashboard_module, name))


def test_batch100_dashboard_schemas_defined_and_exported():
    import app.schemas.dashboard as dashboard_schemas

    src = _read("backend/app/schemas/dashboard.py")
    for cls in (
        "InvoiceSettlementAuditItem",
        "InvoiceSettlementAuditResponse",
        "RefundAuditItem",
        "RefundAuditResponse",
    ):
        assert f"class {cls}(BaseSchema):" in src
        assert cls in dashboard_schemas.__all__

    for field in ("settled_amount", "outstanding_amount", "is_cleared", "cleared_count"):
        assert field in src
    for field in ("refund_amount", "has_remarks", "invoice_exists", "processing_complete"):
        assert field in src


def test_batch100_dashboard_schema_validation_round_trip():
    from app.schemas.dashboard import InvoiceSettlementAuditResponse, RefundAuditResponse

    settlement = InvoiceSettlementAuditResponse(
        as_of=date(2026, 10, 5),
        items=[
            {
                "invoice_id": 1,
                "invoice_number": "INV-0001",
                "invoice_date": datetime(2026, 10, 4, 9, 0, 0),
                "patient_id": 11,
                "patient_name": "Ann Test",
                "total_amount": "500",
                "total_paid": "500",
                "settled_amount": "500",
                "outstanding_amount": "0",
                "overpayment_amount": "0",
                "payment_count": 1,
                "refund_count": 0,
                "stored_payment_status": "paid",
                "derived_payment_status": "paid",
                "status_matches": True,
                "is_cleared": True,
            }
        ],
        total_invoices=1,
        cleared_count=1,
        unsettled_count=0,
        total_billed="500",
        total_collected="500",
        total_outstanding="0",
    )
    assert settlement.items[0].settled_amount == Decimal("500")

    refunds = RefundAuditResponse(
        as_of=date(2026, 10, 5),
        items=[
            {
                "payment_id": 1,
                "receipt_number": "RCT-0001",
                "payment_datetime": datetime(2026, 10, 4, 12, 0, 0),
                "payment_method": "cash",
                "refund_amount": "50",
                "invoice_id": 11,
                "invoice_number": "INV-0011",
                "invoice_total_amount": "500",
                "invoice_net_paid": "450",
                "received_by": 7,
                "has_remarks": True,
                "invoice_exists": True,
                "net_non_negative": True,
                "processing_complete": True,
            }
        ],
        total_refunds=1,
        processed_count=1,
        drifted_count=0,
        total_refunded="50",
    )
    assert refunds.items[0].processing_complete is True


# ---------------------------------------------------------------------------
# Print envelope schemas
# ---------------------------------------------------------------------------


BATCH100_PRINT_CLASSES = (
    "InvoiceSettlementAuditPrintRequest",
    "InvoiceSettlementAuditPrintLine",
    "InvoiceSettlementAuditPrintData",
    "InvoiceSettlementAuditPrintEnvelope",
    "RefundAuditPrintRequest",
    "RefundAuditPrintLine",
    "RefundAuditPrintData",
    "RefundAuditPrintEnvelope",
    "DischargeAuditPrintRequest",
    "DischargeAuditPrintLine",
    "DischargeAuditPrintData",
    "DischargeAuditPrintEnvelope",
    "OPDQueueSummaryPrintRequest",
    "OPDQueueSummaryPrintLine",
    "OPDQueueSummaryPrintData",
    "OPDQueueSummaryPrintEnvelope",
)


def test_batch100_print_schemas_defined_and_exported():
    import app.schemas.reporting as reporting_schemas

    src = _read("backend/app/schemas/reporting.py")
    for cls in BATCH100_PRINT_CLASSES:
        assert f"class {cls}(BaseSchema):" in src, cls
        assert cls in reporting_schemas.__all__, cls


def _field_bound(field, bound_type):
    """Pull a numeric bound (Ge/Le) out of a Pydantic v2 FieldInfo."""
    for constraint in field.metadata:
        if isinstance(constraint, bound_type):
            return getattr(constraint, bound_type.__name__.lower())
    return None


def test_batch100_print_request_bounds_and_report_types():
    from pydantic import Ge, Le, ValidationError

    from app.schemas.reporting import (
        DischargeAuditPrintRequest,
        InvoiceSettlementAuditPrintEnvelope,
        InvoiceSettlementAuditPrintRequest,
        OPDQueueSummaryPrintRequest,
        RefundAuditPrintEnvelope,
        InvoiceSettlementAuditPrintEnvelope as SettlementEnvelope,
    )

    # bounded limits match the dashboard feeds
    assert InvoiceSettlementAuditPrintEnvelope.model_fields["report_type"].default == (
        "invoice_settlement_audit_print"
    )
    assert RefundAuditPrintEnvelope.model_fields["report_type"].default == (
        "refund_audit_print"
    )
    limit_field = DischargeAuditPrintRequest.model_fields["limit"]
    assert _field_bound(limit_field, Ge) == 1
    assert _field_bound(limit_field, Le) == 500
    days_field = OPDQueueSummaryPrintRequest.model_fields["limit_days"]
    assert days_field.default == 14
    assert _field_bound(days_field, Le) == 90
    assert SettlementEnvelope.model_fields["report_type"].default == (
        "invoice_settlement_audit_print"
    )
    with pytest.raises(ValidationError):
        OPDQueueSummaryPrintRequest(limit_days=0)
    with pytest.raises(ValidationError):
        InvoiceSettlementAuditPrintRequest(limit=501)


# ---------------------------------------------------------------------------
# Service layer: envelopes reuse the shared scans (screen/paper parity)
# ---------------------------------------------------------------------------


def test_batch100_service_envelopes_reuse_shared_scans():
    src = _read("backend/app/services/reporting.py")
    for method, scan in (
        (
            "build_invoice_settlement_audit_print_envelope",
            "build_invoice_settlement_audit_scan",
        ),
        ("build_refund_audit_print_envelope", "build_refund_audit_scan"),
        ("build_discharge_audit_print_envelope", "build_discharge_audit_scan"),
        ("build_opd_queue_summary_print_envelope", "build_opd_queue_summary_scan"),
    ):
        assert f"async def {method}" in src, method
        assert scan in src, scan
    # discharge envelope also reuses the Batch 99 pure derivation verbatim
    assert "build_discharge_audit_result(" in src
    # amounts stringify Decimals per the print-schema convention
    assert "str(audit[\"total_billed\"])" in src
    assert "str(audit[\"total_refunded\"])" in src


def test_batch100_print_endpoints_registered_with_response_models():
    src = _read("backend/app/api/v1/endpoints/reporting.py")
    for path, model in (
        (
            '"/invoice-settlement-audit-print-envelope"',
            "InvoiceSettlementAuditPrintEnvelope",
        ),
        ('"/refund-audit-print-envelope"', "RefundAuditPrintEnvelope"),
        ('"/discharge-audit-print-envelope"', "DischargeAuditPrintEnvelope"),
        ('"/opd-queue-summary-print-envelope"', "OPDQueueSummaryPrintEnvelope"),
    ):
        assert path in src, path
        assert f"response_model={model}" in src, model


def test_batch100_routes_present_on_application():
    from app.main import app

    paths = {route.path for route in app.routes}
    for path in (
        "/api/v1/dashboard/invoice-settlement-audit",
        "/api/v1/dashboard/refund-audit",
        "/api/v1/reports/invoice-settlement-audit-print-envelope",
        "/api/v1/reports/refund-audit-print-envelope",
        "/api/v1/reports/discharge-audit-print-envelope",
        "/api/v1/reports/opd-queue-summary-print-envelope",
    ):
        assert path in paths, path


# ---------------------------------------------------------------------------
# Frontend wiring
# ---------------------------------------------------------------------------


def test_frontend_api_wrappers_target_batch100_routes():
    src = _read("frontend/js/api.js")
    assert "export async function getDashboardInvoiceSettlementAudit" in src
    assert "/api/v1/dashboard/invoice-settlement-audit" in src
    assert "export async function getDashboardRefundAudit" in src
    assert "/api/v1/dashboard/refund-audit" in src
    for fn, route in (
        ("buildInvoiceSettlementAuditPrintEnvelope", "invoice-settlement-audit-print-envelope"),
        ("buildRefundAuditPrintEnvelope", "refund-audit-print-envelope"),
        ("buildDischargeAuditPrintEnvelope", "discharge-audit-print-envelope"),
        ("buildOPDQueueSummaryPrintEnvelope", "opd-queue-summary-print-envelope"),
    ):
        assert f"export async function {fn}" in src, fn
        assert f"/api/v1/reports/{route}" in src, route


def test_frontend_print_renderers_exported():
    src = _read("frontend/js/print.js")
    for fn in (
        "createInvoiceSettlementAuditPrintPreview",
        "createRefundAuditPrintPreview",
        "createDischargeAuditPrintPreview",
        "createOPDQueueSummaryPrintPreview",
    ):
        assert f"export function {fn}" in src, fn


def test_reports_workspace_cards_and_handlers():
    src = _read("frontend/js/reports.js")
    # imports pulled through from api.js / print.js
    for symbol in (
        "buildInvoiceOverpaymentPrintEnvelope",
        "buildInvoiceSettlementAuditPrintEnvelope",
        "buildRefundAuditPrintEnvelope",
        "buildDischargeAuditPrintEnvelope",
        "buildOPDQueueSummaryPrintEnvelope",
        "createInvoiceOverpaymentPrintPreview",
        "createInvoiceSettlementAuditPrintPreview",
        "createRefundAuditPrintPreview",
        "createDischargeAuditPrintPreview",
        "createOPDQueueSummaryPrintPreview",
    ):
        assert symbol in src, symbol
    # every card id referenced by a handler selector exists in the template
    for card_id in (
        "overpayment-limit",
        "settlement-audit-limit",
        "refund-audit-limit",
        "discharge-audit-limit",
        "queue-summary-days",
    ):
        assert f'id="{card_id}"' in src or f'id=\\"{card_id}\\"' in src, card_id
        assert f'"#{card_id}"' in src, card_id
    for prepare_id in (
        "overpayment-prepare",
        "settlement-audit-prepare",
        "refund-audit-prepare",
        "discharge-audit-prepare",
        "queue-summary-prepare",
    ):
        assert f'id="{prepare_id}"' in src or f'id=\\"{prepare_id}\\"' in src, prepare_id
        assert f'"#{prepare_id}"' in src, prepare_id


def test_batch97_overpayment_ghost_card_closed():
    """The Batch 97 overpayment ledger was server-complete but had no UI card.

    Batch 100 wires it into the Reports & Printing workspace; lock that the
    card, handler and renderer call are all present so the surface can never
    silently detach from the UI again.
    """
    src = _read("frontend/js/reports.js")
    assert "Invoice overpayment ledger" in src
    assert "buildInvoiceOverpaymentPrintEnvelope" in src
    assert "createInvoiceOverpaymentPrintPreview" in src


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------


def test_batch100_documentation_exists_and_indexed():
    doc = ROOT / "docs" / "CLIENT_BATCH100_SETTLEMENT_REFUND_AUDIT_PRINT_ENVELOPES.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "/dashboard/invoice-settlement-audit" in text
    assert "/dashboard/refund-audit" in text
    assert "/reports/invoice-settlement-audit-print-envelope" in text
    assert "/reports/refund-audit-print-envelope" in text
    assert "/reports/discharge-audit-print-envelope" in text
    assert "/reports/opd-queue-summary-print-envelope" in text
    index = _read("docs/INDEX.md")
    assert "CLIENT_BATCH100_SETTLEMENT_REFUND_AUDIT_PRINT_ENVELOPES.md" in index
    changelog = _read("CHANGELOG.md")
    assert "Batch 100" in changelog


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
