"""
Financial reconciliation: Does the money reconcile, and who authorised it.

Split out of ``dashboard.py`` so that each report is guarded by the permission that
matches the question it answers. Twelve of the eighteen routes were about money and all
of them shared one guard, which let a laboratory technician read the refund audit.

The computation lives in ``dashboard.py``; this module only exposes it.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from sqlalchemy import func, select

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.permissions import require
from app.dependencies.database import DatabaseSession
from app.models.admission import Admission
from app.models.bed import Bed
from app.models.case_record import CaseRecord
from app.models.discharge import Discharge
from app.models.investigation import Investigation
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.opd_token import OPDToken
from app.models.patient import Patient
from app.models.payment import Payment
from app.schemas.dashboard import (
    InvoiceSettlementAuditResponse,
    RefundAuditResponse,
    BedOccupancyResponse,
    InvestigationBillingReconciliationResponse,
    WardOccupancySummaryItem,
    WardOccupancySummaryResponse,
    DischargeAuditResponse,
    DueFollowUpsResponse,
    InvoiceOverpaymentResponse,
    InvoicePaymentReconciliationResponse,
    InvoiceReceiptContinuityResponse,
    InvoiceSettlementAuditResponse,
    OutstandingInvoicesResponse,
    OPDQueueSummaryResponse,
    PatientCollectionSummaryResponse,
    PaymentMethodOverpaymentResponse,
    PaymentMethodSummaryResponse,
    PendingInvestigationsResponse,
    ReceiptNumberingContinuityResponse,
    ReceivablesAgingResponse,
    RefundAuditResponse,
)
from app.services.billing import billing_service
from app.services.followup import followup_service

# The computations live in ``dashboard``. Bound here so a route reads exactly as it
# did before the split, and so that module stays the only place they are defined.
from app.api.v1.endpoints.dashboard import *  # noqa: F401,F403
from app.api.v1.endpoints.dashboard import (  # noqa: F401 - private helpers
    _RECEIVABLES_BUCKETS,
    _load_continuity_scan_inputs,
    _naive_utc,
    _patient_display_name,
    _receipt_numeric_suffix,
)

router = APIRouter(prefix="/dashboard", tags=["Financial reconciliation"])



@router.get("/outstanding-invoices", response_model=OutstandingInvoicesResponse, dependencies=[Depends(require("reports.financial"))])
async def outstanding_invoices(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=100, ge=1, le=200),
) -> OutstandingInvoicesResponse:
    """Oldest-first unpaid/partial invoices with derived balances.

    Built on the Batch 82 ``billing_service.list_outstanding_invoices`` feed:
    balances are recomputed from live payments (so stale stored statuses and
    cancelled invoices never surface), and each row is enriched with patient
    identity plus an age in days so receivables can be chased directly from
    the dashboard.
    """
    invoices, total_balance = await billing_service.list_outstanding_invoices(
        db, limit=limit
    )

    as_of = date.today()
    patient_ids = {invoice.patient_id for invoice in invoices}
    patients: dict[int, Patient] = {}
    if patient_ids:
        result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        patients = {p.id: p for p in result.scalars()}

    # Per-row paid totals use the same live-payment derivation as the service,
    # so balance_due + amount_paid always reconciles to total_amount.
    paid_by_invoice: dict[int, Decimal] = {}
    if invoices:
        invoice_ids = [invoice.id for invoice in invoices]
        totals_result = await db.execute(
            select(
                Payment.invoice_id,
                func.coalesce(func.sum(Payment.amount_paid), 0),
            )
            .where(Payment.invoice_id.in_(invoice_ids))
            .group_by(Payment.invoice_id)
        )
        paid_by_invoice = {row[0]: Decimal(str(row[1])) for row in totals_result}

    items = []
    for invoice in invoices:
        patient = patients.get(invoice.patient_id)
        invoice_local_date = (
            invoice.invoice_date.astimezone(timezone.utc).date()
            if invoice.invoice_date.tzinfo is not None
            else invoice.invoice_date.date()
        )
        amount_paid = min(
            paid_by_invoice.get(invoice.id, Decimal("0")),
            invoice.total_amount,
        )
        balance_due = max(invoice.total_amount - amount_paid, Decimal("0"))
        items.append(
            {
                "invoice_id": invoice.id,
                "patient_id": invoice.patient_id,
                "patient_name": _patient_display_name(patient),
                "patient_number": patient.patient_number if patient else None,
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date,
                "total_amount": invoice.total_amount,
                "amount_paid": amount_paid,
                "balance_due": balance_due,
                "payment_status": invoice.payment_status,
                "days_outstanding": max((as_of - invoice_local_date).days, 0),
            }
        )

    return OutstandingInvoicesResponse(
        as_of=as_of,
        items=items,
        total_outstanding=total_balance,
        invoice_count=len(items),
    )


@router.get("/receivables-aging", response_model=ReceivablesAgingResponse, dependencies=[Depends(require("reports.financial"))])
async def receivables_aging(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> ReceivablesAgingResponse:
    """Financial-style receivables aging ledger over live outstanding invoices.

    Batch 86 — reporting/printing integration feed. Built on the same
    Batch 82 ``billing_service.list_outstanding_invoices`` derivation so
    balances always reconcile (``amount_paid + balance_due == total_amount``,
    stale stored statuses and cancelled invoices never surface). Each invoice
    is placed into a standard 0-30/31-60/61-90/90+ aging bucket by its age in
    days; every bucket is reported even when empty so printed ledgers keep a
    stable shape, and bucket counts/totals sum back to the headline aggregates.
    Patient enrichment is batched (no N+1). Batch 91 extracted the bucketing
    into ``build_receivables_aging_result`` so the print envelope reuses the
    exact same code path.
    """
    invoices, _service_total = await billing_service.list_outstanding_invoices(
        db, limit=limit
    )

    as_of = date.today()
    patient_ids = {invoice.patient_id for invoice in invoices}
    patients: dict[int, Patient] = {}
    if patient_ids:
        result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        patients = {p.id: p for p in result.scalars()}

    # Live-payment derivation identical to the Batch 82 outstanding feed.
    paid_by_invoice: dict[int, Decimal] = {}
    if invoices:
        invoice_ids = [invoice.id for invoice in invoices]
        totals_result = await db.execute(
            select(
                Payment.invoice_id,
                func.coalesce(func.sum(Payment.amount_paid), 0),
            )
            .where(Payment.invoice_id.in_(invoice_ids))
            .group_by(Payment.invoice_id)
        )
        paid_by_invoice = {row[0]: Decimal(str(row[1])) for row in totals_result}

    return ReceivablesAgingResponse(
        **build_receivables_aging_result(invoices, patients, paid_by_invoice, as_of)
    )


@router.get("/invoice-receipt-continuity", response_model=InvoiceReceiptContinuityResponse, dependencies=[Depends(require("reports.financial"))])
async def invoice_receipt_continuity(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> InvoiceReceiptContinuityResponse:
    """Audit invoice-to-receipt numbering continuity on live billing data.

    Batch 87 — reporting/printing integration feed; Batch 92 moved the
    derivation into the shared ``build_invoice_receipt_continuity_result``
    helper so the printable envelope can never drift from this screen feed.
    """
    invoices, patients, receipts_by_invoice, paid_by_invoice = (
        await _load_continuity_scan_inputs(db, limit)
    )
    return InvoiceReceiptContinuityResponse(
        **build_invoice_receipt_continuity_result(
            invoices,
            patients,
            receipts_by_invoice,
            paid_by_invoice,
            datetime.now(timezone.utc),
        )
    )


@router.get("/receipt-numbering-continuity", response_model=ReceiptNumberingContinuityResponse, dependencies=[Depends(require("reports.financial"))])
async def receipt_numbering_continuity(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=2000, ge=1, le=5000),
) -> ReceiptNumberingContinuityResponse:
    """Audit receipt numbering continuity across the whole receipt book.

    Batch 88 — reporting/printing integration feed. Where Batch 87 checked
    receipts *per invoice*, this scans the most recent ``limit`` live Payment
    ledger rows in a single ordered pass (no N+1) and groups them by numeric
    series — every receipt sharing the same non-digit prefix (e.g. ``R`` in
    ``R000123``), parsed with the Batch 87 ``_receipt_numeric_suffix`` helper
    so both audits agree on what "numeric" means.

    For each series the audit reports:

    * ``missing_numbers`` — values skipped between first and last issued
      number (sequence gaps in the physical receipt book);
    * ``duplicate_numbers`` — receipt numbers recorded more than once;
    * per-series reconciliation that always holds:
      ``expected_count == actual_count + gap_count``.

    Non-numeric receipt numbers are counted as checked but never produce
    false gaps, and aggregates (``clean_series_count``, ``total_gap_count``)
    sum back to the scanned ledger so printed audits reconcile.
    """
    audit = await build_receipt_numbering_continuity_result(db, limit)
    return ReceiptNumberingContinuityResponse(**audit)


@router.get("/invoice-payment-reconciliation", response_model=InvoicePaymentReconciliationResponse, dependencies=[Depends(require("reports.financial"))])
async def invoice_payment_reconciliation(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> InvoicePaymentReconciliationResponse:
    """Reconcile recent invoices against the live Payment ledger.

    Batch 89 — reporting/printing integration feed. Where Batch 82/86 only
    surfaced *outstanding* invoices, this ledger reconciles **every** scanned
    invoice (most recent ``limit`` non-cancelled invoices), keeping the
    Batch 68 clamp invariant on every printed row.

    Each row also carries the derived payment status next to the stored one
    (``is_reconciled`` flags drift between the two) plus the number of
    receipts recorded against the invoice, so billing staff can prove
    collection state line-by-line before printing. Headline aggregates sum
    back to ``invoices_checked`` and the totals satisfy
    ``total_billed == total_paid + total_outstanding``.

    Batch 94 — extracted the scan/aggregation into
    ``build_invoice_payment_reconciliation_ledger`` so the reporting print
    envelope reuses this exact code path.
    """
    ledger = await build_invoice_payment_reconciliation_ledger(db, limit)
    return InvoicePaymentReconciliationResponse(**ledger)


@router.get(
    "/collection-summary-by-patient",
    response_model=PatientCollectionSummaryResponse,
    dependencies=[Depends(require("reports.financial"))],
)
async def collection_summary_by_patient(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> PatientCollectionSummaryResponse:
    """Group the Batch 89 reconciliation ledger into per-patient collections.

    Batch 90 — printable collection summary: every figure derives from the
    same live-payment scan as the reconciliation ledger (single grouped
    Payment pass, no N+1, stored counters never trusted), rolled up per
    patient with billed / collected / outstanding totals, derived
    paid/partial/unpaid invoice counts and the latest payment timestamp.
    Headline aggregates sum back to ``invoices_checked`` /
    ``patients_checked`` and the totals satisfy
    ``total_billed == total_collected + total_outstanding``.
    """
    rows = await _build_reconciliation_rows(db, limit)
    return PatientCollectionSummaryResponse(**build_collection_summary_by_patient(rows))


@router.get("/payment-method-summary", response_model=PaymentMethodSummaryResponse, dependencies=[Depends(require("reports.financial"))])
async def payment_method_summary(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> PaymentMethodSummaryResponse:
    """Group live collections by payment method for the scan window.

    Batch 96 — reporting/printing integration feed. Where Batch 90 answered
    *who still owes*, this answers *how the money arrived*: per-method
    receipt counts, distinct invoices touched, gross received versus
    collected (clamped per invoice, Batch 68 parity) and each method's
    percentage share of the window's collected total. Headline aggregates
    always satisfy ``sum(per-method collected) == total_collected``.
    """
    result = await build_payment_method_summary_result(db, limit)
    return PaymentMethodSummaryResponse(**result)


@router.get("/invoice-overpayments", response_model=InvoiceOverpaymentResponse, dependencies=[Depends(require("reports.financial"))])
async def invoice_overpayments(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> InvoiceOverpaymentResponse:
    """List invoices whose live payment ledger exceeds the billed amount.

    Batch 97 — reporting/printing integration feed. The Batch 89/94
    reconciliation ledger clamps ``amount_paid`` to ``total_amount``, which
    deliberately hides over-collection; this feed surfaces exactly what the
    clamp conceals: for the most recent ``limit`` non-cancelled invoices,
    every invoice where the summed Payment rows exceed ``total_amount``,
    with the un-clamped paid total and the resulting ``overpaid_amount``.
    Semantics are derived from the live ledger only (stored counters and
    status columns are never trusted), and the invariant
    ``overpaid_amount == total_paid_raw - total_amount`` holds on every row.
    """
    ledger = await build_overpayment_ledger(db, limit)
    return InvoiceOverpaymentResponse(**ledger)


@router.get(
    "/payment-method-overpayments",
    response_model=PaymentMethodOverpaymentResponse,
    dependencies=[Depends(require("reports.financial"))],
)
async def payment_method_overpayments(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> PaymentMethodOverpaymentResponse:
    """Split the window's over-collection across payment methods.

    Batch 98 — reporting/printing integration feed. Where Batch 97 answers
    *which invoices* were paid beyond their billed amount, this answers
    *which methods* produced the excess: per-method gross received,
    collected (Batch 68 clamp parity via the shared Batch 96 rollup) and
    overpaid figures, with each method's share of the window's collected
    total. Headline aggregates always satisfy ``total_gross ==
    total_collected + total_overpaid`` and ``sum(per-method overpaid) ==
    total_overpaid``.
    """
    result = await build_payment_method_overpayment_result(db, limit)
    return PaymentMethodOverpaymentResponse(**result)


@router.get(
    "/invoice-settlement-audit", response_model=InvoiceSettlementAuditResponse,
    dependencies=[Depends(require("reports.financial"))],
)
async def invoice_settlement_audit(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> InvoiceSettlementAuditResponse:
    """Cleared vs unsettled settlement audit over the live payment ledger.

    Batch 100 — billing settlement mega-batch feed. Where the Batch 89/94
    reconciliation ledger reports clamped paid-vs-balance figures, this
    audit answers *has this invoice fully settled end-to-end*: every
    scanned invoice carries its un-clamped live paid total (refunds
    included as negative payments), the settled/outstanding split, any
    overpayment remainder, receipt and refund counts, and the
    derived-vs-stored status pair. Headlines always satisfy
    ``cleared_count + unsettled_count == total_invoices`` and
    ``total_billed == total_collected + total_outstanding``.
    """
    result = await build_invoice_settlement_audit_scan(db, limit)
    return InvoiceSettlementAuditResponse(**result)


@router.get("/refund-audit", response_model=RefundAuditResponse, dependencies=[Depends(require("reports.financial"))])
async def refund_audit(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> RefundAuditResponse:
    """Every recorded refund inspected for processing drift.

    Batch 100 — billing settlement mega-batch feed. Negative ledger
    entries record refunds/adjustments against live invoices; this audit
    proves each one completed the workflow: invoice link intact, remarks
    note present, and the invoice's net collections left non-negative.
    Drifted refunds stay visible with the failing flags so cash-office
    issues surface before they reach the printed books. Headlines always
    satisfy ``processed_count + drifted_count == total_refunds``.
    """
    result = await build_refund_audit_scan(db, limit)
    return RefundAuditResponse(**result)


@router.get(
    "/investigation-billing-reconciliation",
    response_model=InvestigationBillingReconciliationResponse,
    dependencies=[Depends(require("reports.financial"))],
)
async def investigation_billing_reconciliation(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=1000),
) -> InvestigationBillingReconciliationResponse:
    """Prove every open lab order still has its billed amount on live billing.

    Batch 102 — reconciles the Batch 84 pending-investigation vocabulary
    against ``InvoiceItem`` lines on live non-cancelled invoices: billed
    amounts are re-derived from line totals in one grouped pass (never
    trusted from stored counters), each row keeps ``billed_amount ==
    charged_total - credited_total``, and the headlines keep
    ``pending_count + in_progress_count == total_investigations_checked``
    plus ``billed_count + billed_missing_count ==
    total_investigations_checked``. Unbilled investigations surface with
    ``billed_amount == 0`` instead of disappearing — the same
    drift-surfacing philosophy as the Batch 89/97 ledgers.
    """
    result = await build_investigation_billing_reconciliation(db, limit)
    return InvestigationBillingReconciliationResponse(**result)

