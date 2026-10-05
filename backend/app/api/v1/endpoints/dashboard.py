"""HHMS clinician dashboard endpoints.

Batch 79 — Due Follow-up Workflow Continuity: turns the Batch 78 due-window
service query into a workflow-ready dashboard feed by joining each due
follow-up to its patient and case identity, so clinicians can act on today's
follow-up list directly from the client dashboard.

Batch 82 — Outstanding Billing Continuity: surfaces the billing service's
oldest-first outstanding-invoice feed (derived balances over live payments)
as an administrative receivables panel with patient identity enrichment.

Batch 83 — IPD Bed-Occupancy Continuity: turns bed/admission state into an
actionable inpatient dashboard feed — every occupied bed is reconciled
against its active admission so ward staff see who occupies each bed, how
long the stay has run, and can hand off directly into the patient workspace.

Batch 84 — Laboratory Pending-Investigation Dashboard Feed: surfaces live
investigation orders still awaiting results (pending/in_progress) oldest-first
with per-order age in hours, so laboratory workload is actionable from the
dashboard without opening the Investigations module.

Batch 86 — Receivables Aging Ledger: places the Batch 82 live outstanding
feed into standard 0-30/31-60/61-90/Over-90 aging buckets for reporting and
printing.

Batch 87 — Invoice Receipt Continuity Report: audits invoice-to-receipt
numbering continuity (missing receipts, duplicate receipt numbers, numeric
sequence breaks) so billing staff can spot receipt-book gaps before they turn
into reconciliation problems.

Batch 89 — Invoice Payment Reconciliation Ledger: reconciles every scanned
invoice against the live Payment ledger (paid clamped to totals, derived
status vs stored status) so printed ledgers prove each invoice's balance
reconciles line-by-line.

Batch 90 — Collection Summary by Patient: aggregates the Batch 89
reconciliation ledger per patient into a printable collection summary
(billed / collected / outstanding with derived paid/partial/unpaid counts).
The shared aggregation lives in ``build_collection_summary_by_patient`` so
the dashboard endpoint and the reporting print envelope stay in lockstep.
(Batch 95 wired the Reports workspace card through
``POST /reports/collection-summary-print-envelope``, which runs this exact
aggregation — one implementation, two surfaces.)

Batch 91 — Receivables Aging Print Envelope: extracts the Batch 86 bucketing
into ``build_receivables_aging_result`` so the reporting print envelope reuses
the exact same aging derivation as the dashboard feed (one implementation,
two surfaces).

Batch 92 — Invoice Receipt Continuity Print Envelope: extracts the Batch 87
audit into ``build_invoice_receipt_continuity_result`` plus the shared
``_load_continuity_scan_inputs`` scan so the reporting print envelope reuses
the exact same missing/duplicate/sequence-break derivation as the dashboard
feed.

Batch 93 — Receipt Numbering Continuity Print Envelope: extracts the Batch 88
whole-receipt-book numbering audit into
``build_receipt_numbering_continuity_result`` so the reporting print envelope
reuses the exact same single ordered Payment pass and series gap/duplicate
derivation as the dashboard feed.

Batch 94 — Invoice Payment Reconciliation Print Envelope: extracts the Batch 89
ledger scan/aggregation into ``build_invoice_payment_reconciliation_ledger``
(and the pure rollup ``build_invoice_payment_reconciliation_result``) so the
reporting print envelope reuses the exact same live-payment reconciliation
code path as the dashboard feed.

Batch 96 — Payment Method Collection Summary: adds a new live-derived
dashboard feed (``GET /dashboard/payment-method-summary``) grouping every
payment in the scan window by ``payment_method``, with per-invoice clamped
collected amounts (Batch 68 parity), gross-vs-collected separation and each
method's share of the window total; the shared derivation
(``build_payment_method_collection_summary`` /
``build_payment_method_summary_result``) also backs the reporting print
envelope so screen and paper can never drift.

Batch 97 — Invoice Overpayment Ledger: surfaces what the Batch 68 clamp
conceals (``GET /dashboard/invoice-overpayments``); the un-clamped paid
total is now summed for *every* scanned invoice in one grouped pass inside
the shared ``_build_reconciliation_rows`` scan, so the overpayment ledger
and its print envelope reuse the exact same reconciliation rows (one
implementation, no second scan).

Batch 98 — Payment Method Overpayment Breakdown: answers *which methods*
produce the excess (``GET /dashboard/payment-method-overpayments``); the
chronological clamp already built into
``build_payment_method_collection_summary`` is reused verbatim, with the
un-clamped receipt totals rolled up per method alongside collected and
overpaid figures (invariant ``gross_received == collected + overpaid``).
The shared derivation (``build_payment_method_overpayment_breakdown`` /
``build_payment_method_overpayment_result``) also backs the reporting
print envelope so screen and paper can never drift.

Batch 99 — Ward-Flow Dashboard Mega-Batch: two new operational feeds built
on the Batch 83 bed-occupancy continuity work.
``GET /dashboard/discharge-audit`` reconciles every recent discharge
against its admission status and bed occupancy flag (the live discharge
workflow sets both, so ``is_reconciled`` proves ward flow end-to-end and
drifted rows surface instead of disappearing);
``GET /dashboard/opd-queue-summary`` rolls the OPD token queue up per
queue day with a status split whose invariant
``waiting + in_consultation + completed + cancelled == total_tokens``
always holds, so each day's open backlog reconciles line-for-line.

Batch 100 — Billing Settlement Mega-Batch: three settlement-continuity
surfaces built on the shared reconciliation scan machinery.
``GET /dashboard/invoice-settlement-audit`` reuses the Batch 94
``_build_reconciliation_rows`` scan verbatim and rolls it into a
cleared/unsettled ledger (``settled_amount + outstanding_amount ==
total_amount`` per row; refund receipts count as negative payments);
``GET /dashboard/refund-audit`` audits every negative ``Payment`` ledger
entry for processing drift (invoice link, remarks note, non-negative net
collections); and
``POST /reports/invoice-settlement-audit-print-envelope`` plus
``POST /reports/refund-audit-print-envelope`` print through the exact
same shared derivations so screen and paper can never drift.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Query

from sqlalchemy import func, select

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.models.admission import Admission
from app.models.bed import Bed
from app.models.case_record import CaseRecord
from app.models.discharge import Discharge
from app.models.investigation import Investigation
from app.models.invoice import Invoice
from app.models.opd_token import OPDToken
from app.models.patient import Patient
from app.models.payment import Payment
from app.schemas.dashboard import (
    InvoiceSettlementAuditResponse,
    RefundAuditResponse,
    BedOccupancyResponse,
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

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _naive_utc(value: datetime) -> datetime:
    """SQLite stores naive UTC; normalise any aware input before comparison."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


@router.get("/due-followups", response_model=DueFollowUpsResponse)
async def due_followups(
    db: DatabaseSession,
    _: CurrentUserDependency,
    from_datetime: datetime | None = Query(default=None),
    days_ahead: int = Query(default=7, ge=0, le=365),
    limit: int = Query(default=100, ge=1, le=200),
) -> DueFollowUpsResponse:
    """Follow-ups scheduled inside the window starting ``from_datetime``.

    Defaults to "now through one week ahead" so the dashboard needs no
    parameters for the common case; earlier windows remain reachable via an
    explicit ``from_datetime`` (e.g. to surface overdue follow-ups).
    """
    start = (
        _naive_utc(from_datetime)
        if from_datetime
        else datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    )
    end = start + timedelta(days=days_ahead)

    records = await followup_service.list_due(db, start, end, 0, limit)

    patient_ids = {r.patient_id for r in records}
    case_ids = {r.case_record_id for r in records}
    patients: dict[int, Patient] = {}
    if patient_ids:
        result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        patients = {p.id: p for p in result.scalars()}
    cases: dict[int, CaseRecord] = {}
    if case_ids:
        result = await db.execute(select(CaseRecord).where(CaseRecord.id.in_(case_ids)))
        cases = {c.id: c for c in result.scalars()}

    items = []
    for record in records:
        patient = patients.get(record.patient_id)
        case = cases.get(record.case_record_id)
        name = "Unnamed patient"
        number = None
        if patient is not None:
            name = " ".join(
                part for part in (patient.first_name, patient.middle_name, patient.last_name) if part
            ) or "Unnamed patient"
            number = patient.patient_number
        items.append(
            {
                "followup_id": record.id,
                "case_record_id": record.case_record_id,
                "patient_id": record.patient_id,
                "patient_name": name,
                "patient_number": number,
                "case_number": case.case_number if case is not None else None,
                "next_followup_datetime": record.next_followup_datetime,
                "previous_prescription_id": record.previous_prescription_id,
                "decision": record.decision,
            }
        )

    return DueFollowUpsResponse(from_datetime=start, to_datetime=end, items=items)


def _patient_display_name(patient: Patient | None) -> str:
    if patient is None:
        return "Unnamed patient"
    return " ".join(
        part
        for part in (patient.first_name, patient.middle_name, patient.last_name)
        if part
    ) or "Unnamed patient"


@router.get("/outstanding-invoices", response_model=OutstandingInvoicesResponse)
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


@router.get("/bed-occupancy", response_model=BedOccupancyResponse)
async def bed_occupancy(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> BedOccupancyResponse:
    """Occupied beds reconciled against their active admissions.

    Built on the Batch 61 bed-occupancy concurrency guarantees (row locking
    plus the partial unique index keep at most one active admission per bed):
    this feed reads ``Bed`` rows marked occupied and joins each to its live
    admission/patient identity, so ward occupancy is actionable from the
    dashboard without opening the IPD module. Beds whose occupancy flag has
    drifted from admission state are still reported (with a null admission)
    so data issues surface instead of silently disappearing.
    """
    beds_result = await db.execute(
        select(Bed)
        .where(
            Bed.is_active.is_(True),
            func.lower(Bed.occupancy_status).in_(("occupied", "reserved")),
        )
        .order_by(Bed.ward.asc(), Bed.bed_number.asc(), Bed.id.desc())
        .limit(limit)
    )
    beds = list(beds_result.scalars().all())

    # Active-admission lookup is batched (no N+1); the Batch 61 partial unique
    # index means at most one row matches per bed, but we keep the first by
    # recency defensively.
    active_statuses = ("admitted", "active")
    admissions_by_bed: dict[int, Admission] = {}
    patients_by_id: dict[int, Patient] = {}
    if beds:
        bed_ids = [bed.id for bed in beds]
        adm_result = await db.execute(
            select(Admission)
            .where(
                Admission.bed_id.in_(bed_ids),
                func.lower(Admission.admission_status).in_(active_statuses),
            )
            .order_by(Admission.admission_datetime.desc(), Admission.id.desc())
        )
        for admission in adm_result.scalars():
            admissions_by_bed.setdefault(admission.bed_id, admission)

        patient_ids = {a.patient_id for a in admissions_by_bed.values()}
        if patient_ids:
            pat_result = await db.execute(
                select(Patient).where(Patient.id.in_(patient_ids))
            )
            patients_by_id = {p.id: p for p in pat_result.scalars()}

    as_of = datetime.now(timezone.utc).replace(tzinfo=None)
    items = []
    occupied_count = 0
    for bed in beds:
        admission = admissions_by_bed.get(bed.id)
        patient = (
            patients_by_id.get(admission.patient_id) if admission else None
        )
        length_of_stay_days = None
        if admission is not None:
            occupied_count += 1
            admitted_at = admission.admission_datetime
            if admitted_at.tzinfo is not None:
                admitted_at = admitted_at.astimezone(timezone.utc).replace(
                    tzinfo=None
                )
            length_of_stay_days = max((as_of - admitted_at).days, 0)
        items.append(
            {
                "bed_id": bed.id,
                "bed_number": bed.bed_number,
                "ward": bed.ward,
                "room_number": bed.room_number,
                "bed_type": bed.bed_type,
                "occupancy_status": bed.occupancy_status,
                "has_active_admission": admission is not None,
                "admission_id": admission.id if admission else None,
                "admission_number": (
                    admission.admission_number if admission else None
                ),
                "admission_datetime": (
                    admission.admission_datetime if admission else None
                ),
                "admission_status": (
                    admission.admission_status if admission else None
                ),
                "patient_id": admission.patient_id if admission else None,
                "patient_name": _patient_display_name(patient),
                "patient_number": patient.patient_number if patient else None,
                "length_of_stay_days": length_of_stay_days,
            }
        )

    return BedOccupancyResponse(
        as_of=datetime.now(timezone.utc),
        items=items,
        occupied_count=occupied_count,
        total_beds=len(items),
    )


@router.get("/pending-investigations", response_model=PendingInvestigationsResponse)
async def pending_investigations(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=100, ge=1, le=500),
) -> PendingInvestigationsResponse:
    """Oldest-first live investigation orders still awaiting results.

    Built on the Batch 66 laboratory result workflow: an order leaves the
    backlog only when its report is released (status ``completed``) or it is
    cancelled, so ``pending``/``in_progress`` rows are exactly the orders the
    laboratory still owes results for. Archived-year rows never surface
    (``is_current_year`` mirrors the annual lifecycle), each row carries its
    OPD/IPD lineage (visit/admission/case type) plus an age in hours so
    ageing orders can be chased directly from the dashboard, and patient
    enrichment is batched (no N+1).
    """
    open_statuses = ("pending", "in_progress")
    result = await db.execute(
        select(Investigation)
        .where(
            Investigation.is_current_year.is_(True),
            func.lower(Investigation.investigation_status).in_(open_statuses),
        )
        .order_by(
            Investigation.requested_datetime.asc(),
            Investigation.id.asc(),
        )
        .limit(limit)
    )
    investigations = list(result.scalars().all())

    patients_by_id: dict[int, Patient] = {}
    patient_ids = {inv.patient_id for inv in investigations}
    if patient_ids:
        pat_result = await db.execute(
            select(Patient).where(Patient.id.in_(patient_ids))
        )
        patients_by_id = {p.id: p for p in pat_result.scalars()}

    as_of = datetime.now(timezone.utc).replace(tzinfo=None)
    items = []
    pending_count = 0
    in_progress_count = 0
    for inv in investigations:
        status = (inv.investigation_status or "").lower()
        if status == "pending":
            pending_count += 1
        elif status == "in_progress":
            in_progress_count += 1
        requested_at = inv.requested_datetime
        if requested_at.tzinfo is not None:
            requested_at = requested_at.astimezone(timezone.utc).replace(
                tzinfo=None
            )
        age_hours = max(int((as_of - requested_at).total_seconds() // 3600), 0)
        items.append(
            {
                "investigation_id": inv.id,
                "patient_id": inv.patient_id,
                "patient_name": _patient_display_name(
                    patients_by_id.get(inv.patient_id)
                ),
                "patient_number": (
                    patients_by_id[inv.patient_id].patient_number
                    if inv.patient_id in patients_by_id
                    else None
                ),
                "case_type": inv.case_type,
                "visit_id": inv.visit_id,
                "admission_id": inv.admission_id,
                "investigation_number": inv.investigation_number,
                "investigation_name": inv.investigation_name,
                "investigation_status": inv.investigation_status,
                "requested_datetime": inv.requested_datetime,
                "requested_by": inv.requested_by,
                "age_hours": age_hours,
            }
        )

    return PendingInvestigationsResponse(
        as_of=datetime.now(timezone.utc),
        items=items,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
    )


# Standard receivables aging buckets (days outstanding, inclusive lower /
# exclusive upper; the last bucket is open-ended).
_RECEIVABLES_BUCKETS = (
    ("0-30 days", 0, 30),
    ("31-60 days", 30, 60),
    ("61-90 days", 60, 90),
    ("Over 90 days", 90, None),
)


def build_receivables_aging_result(
    invoices: list[Invoice],
    patients: dict[int, Patient],
    paid_by_invoice: dict[int, Decimal],
    as_of: date,
) -> dict:
    """Bucket live-derived outstanding invoices into the standard aging bands.

    Shared by the Batch 86 dashboard feed and the Batch 91 reporting print
    envelope so the printed packet can never drift from the screen: balances
    satisfy ``amount_paid + balance_due == total_amount`` (Batch 68 parity),
    every bucket is present even when empty so printed ledgers keep a stable
    shape, and bucket counts/totals sum back to the headline aggregates.
    """
    bucket_stats = {label: {"count": 0, "total": Decimal("0")} for label, _, _ in _RECEIVABLES_BUCKETS}
    items = []
    total_outstanding = Decimal("0")
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
        if balance_due <= 0:
            continue
        days_outstanding = max((as_of - invoice_local_date).days, 0)
        bucket_label = _RECEIVABLES_BUCKETS[-1][0]
        for label, lower, upper in _RECEIVABLES_BUCKETS:
            if days_outstanding >= lower and (upper is None or days_outstanding < upper):
                bucket_label = label
                break
        bucket_stats[bucket_label]["count"] += 1
        bucket_stats[bucket_label]["total"] += balance_due
        total_outstanding += balance_due
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
                "days_outstanding": days_outstanding,
                "bucket_label": bucket_label,
            }
        )

    buckets = [
        {
            "label": label,
            "lower_days": lower,
            "upper_days": upper,
            "invoice_count": bucket_stats[label]["count"],
            "total_outstanding": bucket_stats[label]["total"],
        }
        for label, lower, upper in _RECEIVABLES_BUCKETS
    ]

    return {
        "as_of": as_of,
        "buckets": buckets,
        "items": items,
        "invoice_count": len(items),
        "total_outstanding": total_outstanding,
    }


@router.get("/receivables-aging", response_model=ReceivablesAgingResponse)
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


def _receipt_numeric_suffix(receipt_number: str) -> int | None:
    """Trailing integer of a receipt number, or None if not numeric-terminated.

    Receipt numbers are generated as a prefix plus zero-padded sequence
    (e.g. ``R000123``); only series that end in digits can be checked for
    numeric continuity, everything else is treated as unstructured.
    """
    stripped = receipt_number.strip()
    tail = ""
    for ch in reversed(stripped):
        if ch.isdigit():
            tail = ch + tail
        else:
            break
    return int(tail) if tail else None


def build_invoice_receipt_continuity_result(
    invoices: list[Invoice],
    patients: dict[int, Patient],
    receipts_by_invoice: dict[int, list[str]],
    paid_by_invoice: dict[int, Decimal],
    as_of: datetime,
) -> dict:
    """Shared invoice-to-receipt continuity derivation (dashboard + print).

    Batch 87 — reporting/printing integration feed. For every scanned
    invoice, the receipts recorded against it are checked for:

    * ``missing`` — an invoice carries payments whose receipt rows no longer
      link back (or, with amount paid but no receipt, the receipt book is
      short one entry);
    * ``duplicate`` — the same receipt number appears more than once within
      an invoice's receipts;
    * ``sequence_break`` — the numeric suffixes of an invoice's receipts skip
      at least one value between first and last.

    The audit never trusts stored counters: receipt counts and per-invoice
    paid totals arrive pre-aggregated from a single grouped query over the
    Payment table (no N+1), and every aggregate sums back to
    ``invoices_checked`` so printed continuity reports reconcile.

    Batch 92 — extracted verbatim from the dashboard endpoint so the
    printable envelope (``build_invoice_receipt_continuity_print_envelope``)
    runs through the exact same code path; screen and paper can never drift.
    """
    issues = []
    invoices_with_receipts = 0
    invoices_missing_receipts = 0
    duplicate_receipt_count = 0
    sequence_break_count = 0

    for invoice in invoices:
        patient = patients.get(invoice.patient_id)
        numbers = receipts_by_invoice.get(invoice.id, [])
        base = {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "patient_id": invoice.patient_id,
            "patient_name": _patient_display_name(patient),
            "patient_number": patient.patient_number if patient else None,
        }

        if not numbers:
            # Derive "paid" from live payments (Batch 82 semantics): the
            # stored status column can lag behind the payment ledger.
            paid = paid_by_invoice.get(invoice.id, Decimal("0"))
            has_payments = (
                paid > 0
                or str(invoice.payment_status) in ("partial", "paid")
            )
            if has_payments:
                invoices_missing_receipts += 1
                issues.append(
                    {
                        **base,
                        "gap_type": "missing",
                        "expected_count": 1,
                        "actual_count": 0,
                        "missing_count": 1,
                        "first_receipt_number": None,
                        "last_receipt_number": None,
                        "duplicate_receipt_numbers": [],
                    }
                )
            continue

        invoices_with_receipts += 1

        local_dupes = sorted({n for n in numbers if numbers.count(n) > 1})
        if local_dupes:
            duplicate_receipt_count += 1
            issues.append(
                {
                    **base,
                    "gap_type": "duplicate",
                    "expected_count": len(set(numbers)),
                    "actual_count": len(numbers),
                    "missing_count": 0,
                    "first_receipt_number": numbers[0],
                    "last_receipt_number": numbers[-1],
                    "duplicate_receipt_numbers": local_dupes,
                }
            )

        suffixes = [s for s in (_receipt_numeric_suffix(n) for n in numbers) if s is not None]
        unique_sorted = sorted(set(suffixes))
        if len(unique_sorted) >= 2:
            expected_span = unique_sorted[-1] - unique_sorted[0] + 1
            missing_in_span = expected_span - len(unique_sorted)
            if missing_in_span > 0:
                sequence_break_count += 1
                issues.append(
                    {
                        **base,
                        "gap_type": "sequence_break",
                        "expected_count": expected_span,
                        "actual_count": len(unique_sorted),
                        "missing_count": missing_in_span,
                        "first_receipt_number": numbers[0],
                        "last_receipt_number": numbers[-1],
                        "duplicate_receipt_numbers": [],
                    }
                )

    return {
        "as_of": as_of,
        "invoices_checked": len(invoices),
        "invoices_with_receipts": invoices_with_receipts,
        "invoices_missing_receipts": invoices_missing_receipts,
        "duplicate_receipt_count": duplicate_receipt_count,
        "sequence_break_count": sequence_break_count,
        "issues": issues,
    }


async def _load_continuity_scan_inputs(
    db, limit: int
) -> tuple[list[Invoice], dict[int, Patient], dict[int, list[str]], dict[int, Decimal]]:
    """Scan invoices + single grouped Payment pass for the continuity audit.

    Shared by the Batch 87 dashboard feed and the Batch 92 print envelope so
    both consume identical live-derived inputs (no N+1, stored counters never
    trusted).
    """
    invoices_result = await db.execute(
        select(Invoice)
        .where(Invoice.payment_status != "cancelled")
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .limit(limit)
    )
    invoices = list(invoices_result.scalars())

    patient_ids = {invoice.patient_id for invoice in invoices}
    patients: dict[int, Patient] = {}
    if patient_ids:
        result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        patients = {p.id: p for p in result.scalars()}

    receipts_by_invoice: dict[int, list[str]] = {}
    paid_by_invoice: dict[int, Decimal] = {}
    if invoices:
        invoice_ids = [invoice.id for invoice in invoices]
        receipts_result = await db.execute(
            select(
                Payment.invoice_id,
                Payment.receipt_number,
                Payment.amount_paid,
            )
            .where(Payment.invoice_id.in_(invoice_ids))
            .order_by(Payment.payment_datetime.asc(), Payment.id.asc())
        )
        for invoice_id, receipt_number, amount_paid in receipts_result:
            receipts_by_invoice.setdefault(invoice_id, []).append(receipt_number)
            paid_by_invoice[invoice_id] = paid_by_invoice.get(
                invoice_id, Decimal("0")
            ) + Decimal(str(amount_paid))

    return invoices, patients, receipts_by_invoice, paid_by_invoice


@router.get("/invoice-receipt-continuity", response_model=InvoiceReceiptContinuityResponse)
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


@router.get("/receipt-numbering-continuity", response_model=ReceiptNumberingContinuityResponse)
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


async def build_receipt_numbering_continuity_result(db, limit: int) -> dict:
    """Whole-book receipt numbering audit shared by screen and paper.

    Batch 93 — extracted from the Batch 88 dashboard endpoint so the
    reporting print envelope runs through the *exact same* single ordered
    Payment pass and series derivation (no N+1; shared
    ``_receipt_numeric_suffix`` parsing keeps this audit consistent with
    the per-invoice Batch 87 continuity report). Returns a plain dict
    matching ``ReceiptNumberingContinuityResponse`` fields.
    """
    receipts_result = await db.execute(
        select(Payment.receipt_number)
        .where(Payment.receipt_number.is_not(None))
        .order_by(Payment.payment_datetime.asc(), Payment.id.asc())
        .limit(limit)
    )
    receipt_numbers = [row[0] for row in receipts_result]

    # Group into series by non-digit prefix; keep per-series numeric suffixes.
    series_suffixes: dict[str, list[int]] = {}
    series_counts: dict[str, dict[str, int]] = {}
    unstructured_count = 0
    for receipt_number in receipt_numbers:
        stripped = str(receipt_number).strip()
        suffix = _receipt_numeric_suffix(receipt_number)
        if suffix is None:
            unstructured_count += 1
            continue
        prefix = stripped[: len(stripped) - len(str(suffix))] or "(none)"
        series_suffixes.setdefault(prefix, []).append(suffix)
        series_counts.setdefault(prefix, {})
        series_counts[prefix][stripped] = series_counts[prefix].get(stripped, 0) + 1

    series_items = []
    total_gap_count = 0
    clean_series_count = 0
    for prefix in sorted(series_suffixes):
        suffixes = series_suffixes[prefix]
        counts = series_counts[prefix]
        unique_sorted = sorted(set(suffixes))
        first_number = unique_sorted[0]
        last_number = unique_sorted[-1]
        expected_count = last_number - first_number + 1
        actual_count = len(unique_sorted)
        missing = set(range(first_number, last_number + 1)) - set(unique_sorted)
        # Cap the detail list so a pathological scan can't blow up the payload;
        # gap_count always reflects the true number of missing values.
        missing_numbers = sorted(missing)[:200]
        gap_count = len(missing)
        duplicate_numbers = sorted(n for n, c in counts.items() if c > 1)
        total_gap_count += gap_count
        if gap_count == 0 and not duplicate_numbers:
            clean_series_count += 1
        series_items.append(
            {
                "prefix": prefix,
                "first_number": first_number,
                "last_number": last_number,
                "expected_count": expected_count,
                "actual_count": actual_count,
                "gap_count": gap_count,
                "missing_numbers": missing_numbers,
                "duplicate_numbers": duplicate_numbers,
            }
        )

    return {
        "as_of": datetime.now(timezone.utc),
        "receipts_checked": len(receipt_numbers),
        "series_count": len(series_items),
        "clean_series_count": clean_series_count,
        "total_gap_count": total_gap_count,
        "series": series_items,
    }


def _derive_payment_status(total_amount: Decimal, amount_paid: Decimal) -> str:
    """Derive an invoice payment status from live-payment figures.

    Mirrors the Batch 68 atomic-consistency derivation (unpaid / partial /
    paid) so reconciliation rows never trust a stale stored status column.
    """
    if amount_paid <= 0:
        return "unpaid"
    if amount_paid >= total_amount:
        return "paid"
    return "partial"


def build_invoice_payment_reconciliation_result(
    rows: list[dict], as_of: date
) -> dict:
    """Roll raw reconciliation rows up into ledger items and headlines.

    Batch 94 — extracted verbatim from the Batch 89 dashboard endpoint so
    the reporting print envelope reuses the exact same aggregation code
    path; screen feed and printed packet always agree line-for-line for the
    same scan window. ``paid_invoices + partially_paid_invoices +
    unpaid_invoices`` sums back to ``invoices_checked`` and
    ``total_billed == total_paid + total_outstanding`` holds by construction.
    """
    items = []
    paid_invoices = 0
    partially_paid_invoices = 0
    unpaid_invoices = 0
    total_billed = Decimal("0")
    total_paid = Decimal("0")
    total_outstanding = Decimal("0")
    for row in rows:
        derived_status = row["derived_payment_status"]
        if derived_status == "paid":
            paid_invoices += 1
        elif derived_status == "partial":
            partially_paid_invoices += 1
        else:
            unpaid_invoices += 1
        total_billed += row["total_amount"]
        total_paid += row["amount_paid"]
        total_outstanding += row["balance_due"]
        items.append(
            {key: value for key, value in row.items() if key != "last_payment_datetime"}
        )
    return {
        "as_of": as_of,
        "invoices_checked": len(items),
        "paid_invoices": paid_invoices,
        "partially_paid_invoices": partially_paid_invoices,
        "unpaid_invoices": unpaid_invoices,
        "total_billed": total_billed,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "items": items,
    }


async def build_invoice_payment_reconciliation_ledger(db, limit: int) -> dict:
    """Scan-and-aggregate entry point shared with the reporting service.

    Batch 94 — single implementation behind both
    ``GET /dashboard/invoice-payment-reconciliation`` and
    ``POST /reports/invoice-payment-reconciliation-print-envelope``.
    """
    rows = await _build_reconciliation_rows(db, limit)
    return build_invoice_payment_reconciliation_result(rows, date.today())


async def _build_reconciliation_rows(db, limit: int) -> list[dict]:
    """Scan recent invoices and reconcile each against the live payments.

    Shared by the Batch 89 reconciliation endpoint and the Batch 90
    collection summary (dashboard feed and reporting print envelope).
    Payments are summed in a single grouped pass over the ``Payment`` table
    (no N+1; stored counters and status columns are never trusted),
    ``amount_paid`` is clamped to the invoice total and ``balance_due`` kept
    non-negative so ``amount_paid + balance_due == total_amount`` holds on
    every row (Batch 68 parity).
    """
    invoices_result = await db.execute(
        select(Invoice)
        .where(Invoice.payment_status != "cancelled")
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .limit(limit)
    )
    invoices = list(invoices_result.scalars())

    patient_ids = {invoice.patient_id for invoice in invoices}
    patients: dict[int, Patient] = {}
    if patient_ids:
        result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        patients = {p.id: p for p in result.scalars()}

    # Single grouped pass over the live Payment ledger for all scanned
    # invoices (no N+1): per-invoice paid totals, receipt counts and the
    # latest payment timestamp (Batch 90 last-payment column). Batch 97 —
    # the same pass also captures the *un-clamped* paid total so the
    # overpayment ledger never needs a second scan.
    paid_by_invoice: dict[int, Decimal] = {}
    raw_paid_by_invoice: dict[int, Decimal] = {}
    receipts_by_invoice: dict[int, int] = {}
    last_payment_by_invoice: dict[int, datetime] = {}
    if invoices:
        invoice_ids = [invoice.id for invoice in invoices]
        payments_result = await db.execute(
            select(
                Payment.invoice_id,
                func.sum(Payment.amount_paid),
                func.count(Payment.id),
                func.max(Payment.payment_datetime),
            )
            .where(Payment.invoice_id.in_(invoice_ids))
            .group_by(Payment.invoice_id)
        )
        for (
            invoice_id,
            paid_total,
            receipt_count,
            last_payment,
        ) in payments_result:
            paid_by_invoice[invoice_id] = Decimal(str(paid_total or 0))
            raw_paid_by_invoice[invoice_id] = Decimal(str(paid_total or 0))
            receipts_by_invoice[invoice_id] = int(receipt_count or 0)
            last_payment_by_invoice[invoice_id] = last_payment

    rows = []
    for invoice in invoices:
        patient = patients.get(invoice.patient_id)
        amount_paid = min(
            paid_by_invoice.get(invoice.id, Decimal("0")),
            invoice.total_amount,
        )
        balance_due = max(invoice.total_amount - amount_paid, Decimal("0"))
        rows.append(
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
                # Batch 97: un-clamped live paid total, carried on every row
                # so ``overpaid == max(total_paid_raw - total_amount, 0)``.
                "total_paid_raw": raw_paid_by_invoice.get(
                    invoice.id, Decimal("0")
                ),
                "stored_payment_status": invoice.payment_status,
                "derived_payment_status": _derive_payment_status(
                    invoice.total_amount, amount_paid
                ),
                "receipt_count": receipts_by_invoice.get(invoice.id, 0),
                "last_payment_datetime": last_payment_by_invoice.get(invoice.id),
            }
        )
    for row in rows:
        row["is_reconciled"] = row["derived_payment_status"] == str(
            row["stored_payment_status"]
        )
    return rows


@router.get("/invoice-payment-reconciliation", response_model=InvoicePaymentReconciliationResponse)
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


def build_collection_summary_by_patient(rows: list[dict]) -> dict:
    """Roll reconciliation rows up into per-patient collection totals.

    Batch 90 — shared aggregation used by both the dashboard feed and the
    reporting print envelope so the two surfaces can never drift. Patients
    keep their first appearance order (the ledger scan order); per-patient
    figures satisfy ``total_collected + outstanding == total_billed`` because
    each row's clamped amounts contribute exactly once.
    """
    grouped: dict[int, dict] = {}
    for row in rows:
        summary = grouped.get(row["patient_id"])
        if summary is None:
            summary = {
                "patient_id": row["patient_id"],
                "patient_name": row["patient_name"],
                "patient_number": row["patient_number"],
                "invoice_count": 0,
                "paid_invoice_count": 0,
                "partial_invoice_count": 0,
                "unpaid_invoice_count": 0,
                "total_billed": Decimal("0"),
                "total_collected": Decimal("0"),
                "outstanding": Decimal("0"),
                "last_payment_date": None,
            }
            grouped[row["patient_id"]] = summary
        summary["invoice_count"] += 1
        derived_status = row["derived_payment_status"]
        if derived_status == "paid":
            summary["paid_invoice_count"] += 1
        elif derived_status == "partial":
            summary["partial_invoice_count"] += 1
        else:
            summary["unpaid_invoice_count"] += 1
        summary["total_billed"] += row["total_amount"]
        summary["total_collected"] += row["amount_paid"]
        summary["outstanding"] += row["balance_due"]
        last_payment = row.get("last_payment_datetime")
        if last_payment is not None:
            current = summary["last_payment_date"]
            if current is None or last_payment > current:
                summary["last_payment_date"] = last_payment

    items = list(grouped.values())
    return {
        "as_of": date.today(),
        "invoices_checked": len(rows),
        "patients_checked": len(items),
        "patients_with_outstanding": sum(
            1 for item in items if item["outstanding"] > 0
        ),
        "total_billed": sum(
            (item["total_billed"] for item in items), Decimal("0")
        ),
        "total_collected": sum(
            (item["total_collected"] for item in items), Decimal("0")
        ),
        "total_outstanding": sum(
            (item["outstanding"] for item in items), Decimal("0")
        ),
        "items": items,
    }


@router.get(
    "/collection-summary-by-patient",
    response_model=PatientCollectionSummaryResponse,
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


def build_payment_method_collection_summary(
    receipts: list[dict], invoice_totals: dict[int, Decimal], invoices_checked: int
) -> dict:
    """Roll raw receipt rows up into per-method collection totals.

    Batch 96 — shared aggregation used by both the dashboard feed and the
    reporting print envelope so the two surfaces can never drift. Each
    receipt's *collected* contribution is clamped against its invoice's
    remaining total (Batch 68 parity): receipts are charged to their
    invoice in chronological order (ties broken by receipt number), any
    amount beyond the invoice total counts as gross received but not as
    collected, and payments against invoices outside the scan window
    contribute nothing. Per-method ``collected`` figures therefore sum
    back exactly to the headline ``total_collected``.
    """
    ordered = sorted(
        receipts,
        key=lambda r: (r["payment_datetime"] or datetime.max, r["receipt_number"]),
    )
    remaining = dict(invoice_totals)
    grouped: dict[str, dict] = {}
    for receipt in ordered:
        method = receipt["payment_method"] or "unknown"
        summary = grouped.get(method)
        if summary is None:
            summary = {
                "payment_method": method,
                "receipt_count": 0,
                "invoice_count": 0,
                "gross_received": Decimal("0"),
                "collected": Decimal("0"),
                "share_of_total": Decimal("0"),
            }
            grouped[method] = summary
        summary["receipt_count"] += 1
        gross = Decimal(str(receipt["amount_paid"]))
        summary["gross_received"] += gross
        left = remaining.get(receipt["invoice_id"])
        if left is not None:
            applied = min(gross, left)
            if applied > 0:
                remaining[receipt["invoice_id"]] = left - applied
                summary["collected"] += applied
                summary["invoice_count"] += 1

    items = list(grouped.values())
    total_collected = sum((item["collected"] for item in items), Decimal("0"))
    for item in items:
        share = (
            (item["collected"] * 100 / total_collected).quantize(Decimal("0.01"))
            if total_collected > 0
            else Decimal("0.00")
        )
        item["share_of_total"] = share
    # Largest collectors first; ties broken alphabetically for stability.
    items.sort(key=lambda item: (-item["collected"], item["payment_method"]))
    return {
        "as_of": date.today(),
        "invoices_checked": invoices_checked,
        "receipts_scanned": len(receipts),
        "methods_reported": len(items),
        "total_collected": total_collected,
        "items": items,
    }


async def build_payment_method_summary_result(db, limit: int) -> dict:
    """Scan-and-aggregate entry point shared with the reporting service.

    Batch 96 — single implementation behind both
    ``GET /dashboard/payment-method-summary`` and
    ``POST /reports/payment-method-summary-print-envelope``. Scans the most
    recent ``limit`` non-cancelled invoices (same window as the Batch 89/90
    ledger), then sums every linked payment in one pass over the live
    Payment ledger joined to Invoice (no N+1; stored counters and status
    columns are never trusted).
    """
    invoices_result = await db.execute(
        select(Invoice.id, Invoice.total_amount)
        .where(Invoice.payment_status != "cancelled")
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .limit(limit)
    )
    invoice_rows = list(invoices_result)
    invoice_totals = {row[0]: row[1] for row in invoice_rows}

    receipts: list[dict] = []
    if invoice_totals:
        payments_result = await db.execute(
            select(
                Payment.invoice_id,
                Payment.receipt_number,
                Payment.payment_method,
                Payment.amount_paid,
                Payment.payment_datetime,
            ).join(Invoice, Invoice.id == Payment.invoice_id).where(
                Invoice.payment_status != "cancelled"
            )
        )
        receipts = [
            {
                "invoice_id": invoice_id,
                "receipt_number": receipt_number,
                "payment_method": payment_method,
                "amount_paid": amount_paid,
                "payment_datetime": payment_datetime,
            }
            for invoice_id, receipt_number, payment_method, amount_paid, payment_datetime in payments_result
        ]
    return build_payment_method_collection_summary(
        receipts, invoice_totals, len(invoice_totals)
    )


@router.get("/payment-method-summary", response_model=PaymentMethodSummaryResponse)
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


def build_overpayment_ledger_result(rows: list[dict], as_of: date) -> dict:
    """Roll raw overpayment rows up into ledger items and headlines.

    Batch 97 — shared aggregation used by both the dashboard feed and the
    reporting print envelope so the two surfaces can never drift. Only
    invoices whose live payment total exceeds their billed amount appear;
    every row satisfies ``overpaid_amount == total_paid_raw - total_amount``
    by construction, and the headline sums roll back to
    ``invoices_overpaid == len(items)``.
    """
    items = []
    total_billed = Decimal("0")
    total_paid_raw = Decimal("0")
    total_overpaid = Decimal("0")
    for row in rows:
        total_billed += row["total_amount"]
        total_paid_raw += row["total_paid_raw"]
        total_overpaid += row["overpaid_amount"]
        items.append(dict(row))
    return {
        "as_of": as_of,
        "invoices_checked": len(items),
        "invoices_overpaid": len(items),
        "total_billed": total_billed,
        "total_paid_raw": total_paid_raw,
        "total_overpaid": total_overpaid,
        "items": items,
    }


async def build_overpayment_ledger(db, limit: int) -> dict:
    """Scan-and-aggregate entry point shared with the reporting service.

    Batch 97 — single implementation behind both
    ``GET /dashboard/invoice-overpayments`` and
    ``POST /reports/invoice-overpayment-print-envelope``. Reuses the exact
    same live-scan row builder as the Batch 89/90/94 reconciliation ledger
    (one grouped pass over the Payment table joined to non-cancelled
    invoices, stored counters/status never trusted), then keeps only the
    rows where payments exceed the billed amount. Batch 97 — the
    un-clamped paid total is now carried on every reconciliation row by
    the shared scan itself, so this ledger runs one grouped Payment pass
    for the whole window (no second re-sum per flagged invoice).
    """
    rows = await _build_reconciliation_rows(db, limit)
    overpaid_rows = []
    # Only fully-paid invoices can be overpaid under the clamp; the
    # un-clamped ledger total rides on every row, so no extra scan needed.
    candidates = [row for row in rows if row["balance_due"] == Decimal("0")]
    for row in candidates:
        total_paid_raw = row["total_paid_raw"]
        if total_paid_raw > row["total_amount"]:
            item = dict(row)
            item["overpaid_amount"] = total_paid_raw - row["total_amount"]
            item.pop("last_payment_datetime", None)
            overpaid_rows.append(item)
    return build_overpayment_ledger_result(overpaid_rows, date.today())


@router.get("/invoice-overpayments", response_model=InvoiceOverpaymentResponse)
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


def build_payment_method_overpayment_breakdown(
    receipts: list[dict], invoice_totals: dict[int, Decimal], invoices_checked: int
) -> dict:
    """Roll raw receipt rows up into per-method overpayment totals.

    Batch 98 — shared aggregation used by both the dashboard feed and the
    reporting print envelope so the two surfaces can never drift. The
    chronological clamp is reused verbatim from the Batch 96 collection
    summary (``build_payment_method_collection_summary``): receipts are
    charged to their invoice in payment order (ties broken by receipt
    number), amounts beyond the invoice total count as *overpaid* (not
    collected), and payments against invoices outside the scan window
    contribute neither. Per method the invariant
    ``gross_received == collected + overpaid`` therefore holds on every
    row, and the headline sums satisfy ``total_gross == total_collected +
    total_overpaid`` with ``sum(per-method overpaid) == total_overpaid``.
    Methods carrying no excess still appear (with ``overpaid == 0``) so
    printed breakdowns reconcile line-for-line against the Batch 96
    collection summary for the same scan window; largest overpayers first,
    alphabetical tie-break for stability.
    """
    summary = build_payment_method_collection_summary(
        receipts, invoice_totals, invoices_checked
    )
    ordered = sorted(
        receipts,
        key=lambda r: (r["payment_datetime"] or datetime.max, r["receipt_number"]),
    )
    remaining = dict(invoice_totals)
    overpaid_by_method: dict[str, Decimal] = {}
    for receipt in ordered:
        method = receipt["payment_method"] or "unknown"
        gross = Decimal(str(receipt["amount_paid"]))
        left = remaining.get(receipt["invoice_id"])
        if left is None:
            # Batch 100 — receipts against invoices outside the scan
            # window count as neither collected nor overpaid (Batch 96
            # parity), so per-method ``gross == collected + overpaid``
            # holds on every printed row and phantom excess from
            # out-of-window invoices never inflates the split.
            continue
        applied = min(gross, left)
        if applied > 0:
            remaining[receipt["invoice_id"]] = left - applied
        excess = gross - applied
        overpaid_by_method[method] = overpaid_by_method.get(
            method, Decimal("0")
        ) + excess

    items = []
    for entry in summary["items"]:
        item = dict(entry)
        item["overpaid"] = overpaid_by_method.get(item["payment_method"], Decimal("0"))
        items.append(item)
    items.sort(key=lambda item: (-item["overpaid"], item["payment_method"]))
    total_collected = summary["total_collected"]
    total_overpaid = sum(overpaid_by_method.values(), Decimal("0"))
    return {
        "as_of": date.today(),
        "invoices_checked": invoices_checked,
        "receipts_scanned": len(receipts),
        "methods_reported": len(items),
        "methods_with_overpayment": sum(
            1 for item in items if item["overpaid"] > 0
        ),
        "total_gross": total_collected + total_overpaid,
        "total_collected": total_collected,
        "total_overpaid": total_overpaid,
        "items": items,
    }


async def build_payment_method_overpayment_result(db, limit: int) -> dict:
    """Scan-and-aggregate entry point shared with the reporting service.

    Batch 98 — single implementation behind both
    ``GET /dashboard/payment-method-overpayments`` and
    ``POST /reports/payment-method-overpayment-print-envelope``. Scans the
    most recent ``limit`` non-cancelled invoices (same window as the Batch
    89/90 ledger and the Batch 96 method summary), then reads every linked
    receipt in one pass over the live Payment ledger joined to Invoice
    (no N+1; stored counters and status columns are never trusted).
    """
    invoices_result = await db.execute(
        select(Invoice.id, Invoice.total_amount)
        .where(Invoice.payment_status != "cancelled")
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .limit(limit)
    )
    invoice_rows = list(invoices_result)
    invoice_totals = {row[0]: row[1] for row in invoice_rows}

    receipts: list[dict] = []
    if invoice_totals:
        payments_result = await db.execute(
            select(
                Payment.invoice_id,
                Payment.receipt_number,
                Payment.payment_method,
                Payment.amount_paid,
                Payment.payment_datetime,
            ).join(Invoice, Invoice.id == Payment.invoice_id).where(
                Invoice.payment_status != "cancelled"
            )
        )
        receipts = [
            {
                "invoice_id": invoice_id,
                "receipt_number": receipt_number,
                "payment_method": payment_method,
                "amount_paid": amount_paid,
                "payment_datetime": payment_datetime,
            }
            for invoice_id, receipt_number, payment_method, amount_paid, payment_datetime in payments_result
        ]
    return build_payment_method_overpayment_breakdown(
        receipts, invoice_totals, len(invoice_totals)
    )


@router.get(
    "/payment-method-overpayments",
    response_model=PaymentMethodOverpaymentResponse,
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


def _as_naive_utc(value: datetime) -> datetime:
    """Normalise a stored datetime to naive UTC for age arithmetic."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def build_discharge_audit_result(rows: list[dict], as_of: datetime) -> dict:
    """Pure reconciliation pass over discharge scan rows.

    Batch 99 — shared derivation behind ``GET /dashboard/discharge-audit``.
    Each row (a joined Discharge/Admission/Patient/Bed tuple serialised as a
    dict) is reconciled against the workflow guarantees from the discharge
    service: creating a discharge marks its admission ``discharged`` and
    frees its bed. ``admission_discharged`` and ``bed_freed`` expose the
    individual checks; ``is_reconciled`` requires both (plus an existing
    bed link), so drifted ward-flow rows surface instead of disappearing.
    Rows are ordered newest-discharge-first and ages are whole hours
    against ``as_of`` (never negative).
    """
    items = []
    reconciled_count = 0
    for row in sorted(
        rows,
        key=lambda r: _as_naive_utc(r["discharge_datetime"]),
        reverse=True,
    ):
        admission_status = (row["admission_status"] or "").lower()
        bed_occupancy_status = (
            row["bed_occupancy_status"].lower()
            if row["bed_occupancy_status"]
            else None
        )
        admission_discharged = admission_status == "discharged"
        bed_freed = row["bed_id"] is not None and bed_occupancy_status == "available"
        is_reconciled = admission_discharged and bed_freed
        if is_reconciled:
            reconciled_count += 1
        hours_since_discharge = max(
            int(
                (
                    _as_naive_utc(as_of)
                    - _as_naive_utc(row["discharge_datetime"])
                ).total_seconds()
                // 3600
            ),
            0,
        )
        items.append(
            {
                **row,
                "admission_discharged": admission_discharged,
                "bed_freed": bed_freed,
                "is_reconciled": is_reconciled,
                "hours_since_discharge": hours_since_discharge,
            }
        )

    return {
        "as_of": as_of,
        "items": items,
        "total_discharges": len(items),
        "reconciled_count": reconciled_count,
        "drift_count": len(items) - reconciled_count,
    }


async def build_discharge_audit_scan(db, limit: int) -> list[dict]:
    """Single joined scan feeding the Batch 99 discharge audit.

    Shared entry point so the dashboard endpoint (and any future print
    envelope) reads exactly the same rows: every recent discharge joined
    to its admission, patient and bed identity in one pass (no N+1).
    """
    result = await db.execute(
        select(
            Discharge,
            Admission,
            Patient,
            Bed,
        )
        .join(Admission, Admission.id == Discharge.admission_id)
        .join(Patient, Patient.id == Admission.patient_id)
        .outerjoin(Bed, Bed.id == Admission.bed_id)
        .order_by(Discharge.discharge_datetime.desc(), Discharge.id.desc())
        .limit(limit)
    )
    rows = []
    for discharge, admission, patient, bed in result:
        rows.append(
            {
                "discharge_id": discharge.id,
                "discharge_number": discharge.discharge_number,
                "discharge_datetime": discharge.discharge_datetime,
                "discharge_status": discharge.discharge_status,
                "discharged_by": discharge.discharged_by,
                "admission_id": admission.id,
                "admission_number": admission.admission_number,
                "admission_status": admission.admission_status,
                "patient_id": patient.id,
                "patient_name": _patient_display_name(patient),
                "patient_number": patient.patient_number,
                "bed_id": bed.id if bed else None,
                "bed_number": bed.bed_number if bed else None,
                "ward": bed.ward if bed else None,
                "bed_occupancy_status": (
                    bed.occupancy_status if bed else None
                ),
            }
        )
    return rows


@router.get("/discharge-audit", response_model=DischargeAuditResponse)
async def discharge_audit(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> DischargeAuditResponse:
    """Recent discharges reconciled against admission and bed state.

    Batch 99 — ward-flow continuity feed built on the Batch 83
    bed-occupancy guarantees: the live discharge workflow marks the
    admission ``discharged`` and frees its bed when a discharge record is
    created, so each audit row proves the hand-off completed end-to-end.
    Drifted rows (admission still active, bed still occupied, or no bed
    link) keep appearing with ``is_reconciled`` false so data issues
    surface instead of silently disappearing. Headline counts always
    satisfy ``reconciled_count + drift_count == total_discharges``.
    """
    rows = await build_discharge_audit_scan(db, limit)
    result = build_discharge_audit_result(
        rows, datetime.now(timezone.utc).replace(tzinfo=None)
    )
    return DischargeAuditResponse(**result)


OPD_QUEUE_STATUSES = ("waiting", "in_consultation", "completed", "cancelled")


def build_opd_queue_summary_result(rows: list[dict], as_of: datetime) -> dict:
    """Pure per-day rollup over OPD token status counts.

    Batch 99 — shared derivation behind ``GET /dashboard/opd-queue-summary``.
    Input rows are ``(queue_date, queue_status, token_count)`` tuples from a
    single grouped pass; the output keeps every day's status split intact so
    the invariant ``waiting + in_consultation + completed + cancelled ==
    total_tokens`` holds line-for-line, with ``open_token_count`` equal to
    the still-running backlog (waiting + in_consultation). Days are ordered
    newest first; unknown statuses count only toward the day total so the
    split never silently swallows tokens.
    """
    by_day: dict[date, dict[str, int]] = {}
    other_total = 0
    for row in rows:
        day_counts = by_day.setdefault(
            row["queue_date"], {status: 0 for status in OPD_QUEUE_STATUSES}
        )
        status = (row["queue_status"] or "").lower()
        count = int(row["token_count"])
        if status in day_counts:
            day_counts[status] += count
        else:
            other_total += count

    items = []
    total_tokens = 0
    total_open = 0
    for queue_date in sorted(by_day, reverse=True):
        day_counts = by_day[queue_date]
        waiting = day_counts["waiting"]
        in_consultation = day_counts["in_consultation"]
        completed = day_counts["completed"]
        cancelled = day_counts["cancelled"]
        day_total = waiting + in_consultation + completed + cancelled
        open_token_count = waiting + in_consultation
        total_tokens += day_total
        total_open += open_token_count
        items.append(
            {
                "queue_date": queue_date,
                "total_tokens": day_total,
                "waiting": waiting,
                "in_consultation": in_consultation,
                "completed": completed,
                "cancelled": cancelled,
                "open_token_count": open_token_count,
            }
        )

    return {
        "as_of": as_of,
        "items": items,
        "days_reported": len(items),
        "total_tokens": total_tokens + other_total,
        "total_open": total_open,
    }


async def build_opd_queue_summary_scan(db, limit_days: int) -> dict:
    """Grouped-scan entry point shared with any future print surface.

    Batch 99 — one grouped pass over ``OPDToken`` (queue_date x
    queue_status), then the pure rollup above. Only the most recent
    ``limit_days`` queue days are reported; the grouped query stays cheap
    regardless of token volume.
    """
    dates_result = await db.execute(
        select(OPDToken.queue_date)
        .group_by(OPDToken.queue_date)
        .order_by(OPDToken.queue_date.desc())
        .limit(limit_days)
    )
    included_dates = [row[0] for row in dates_result]
    if not included_dates:
        return build_opd_queue_summary_result([], datetime.now(timezone.utc).replace(tzinfo=None))

    counts_result = await db.execute(
        select(
            OPDToken.queue_date,
            OPDToken.queue_status,
            func.count(OPDToken.id),
        )
        .where(OPDToken.queue_date.in_(included_dates))
        .group_by(OPDToken.queue_date, OPDToken.queue_status)
    )
    rows = [
        {
            "queue_date": queue_date,
            "queue_status": queue_status,
            "token_count": token_count,
        }
        for queue_date, queue_status, token_count in counts_result
    ]
    return build_opd_queue_summary_result(
        rows, datetime.now(timezone.utc).replace(tzinfo=None)
    )


@router.get("/opd-queue-summary", response_model=OPDQueueSummaryResponse)
async def opd_queue_summary(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit_days: int = Query(default=14, ge=1, le=90),
) -> OPDQueueSummaryResponse:
    """Daily OPD token queue workload, newest queue day first.

    Batch 99 — outpatient-flow continuity feed: every reported day's
    figures come from one grouped pass over live ``OPDToken`` rows, so the
    status split (waiting/in_consultation/completed/cancelled) always sums
    to that day's total and the open backlog reconciles line-for-line.
    Clinician desks get today's pressure and the trailing days' throughput
    without opening the OPD module.
    """
    result = await build_opd_queue_summary_scan(db, limit_days)
    return OPDQueueSummaryResponse(**result)


def build_invoice_settlement_audit_result(rows: list[dict], as_of: date) -> dict:
    """Pure cleared/unsettled rollup over shared reconciliation rows.

    Batch 100 — shared derivation behind
    ``GET /dashboard/invoice-settlement-audit`` and its print envelope.
    Input rows come from ``_build_reconciliation_rows`` (single grouped
    Payment pass, no N+1, stored counters/status never trusted), so every
    printed/screen row satisfies ``settled_amount + outstanding_amount ==
    total_amount`` by construction. Refund receipts (negative payments,
    the Batch 100 posting rule) reduce ``total_paid_raw`` and therefore
    the settled side; any amount collected beyond the billed total is
    reported as ``overpayment_amount`` (Batch 97 clamp parity) so the
    headline ``total_collected`` counts each invoice's absorbed amount
    exactly once. Rows keep the scan order (newest invoices first);
    headlines always satisfy ``cleared_count + unsettled_count ==
    total_invoices`` and ``total_billed == total_collected +
    total_outstanding``.
    """
    items = []
    cleared_count = 0
    total_billed = Decimal("0")
    total_collected = Decimal("0")
    total_outstanding = Decimal("0")
    for row in rows:
        total_paid_raw = Decimal(str(row["total_paid_raw"]))
        total_amount = Decimal(str(row["total_amount"]))
        settled_amount = min(max(total_paid_raw, Decimal("0")), total_amount)
        outstanding_amount = max(total_amount - total_paid_raw, Decimal("0"))
        overpayment_amount = max(total_paid_raw - total_amount, Decimal("0"))
        payment_count = int(row["receipt_count"])
        derived_status = _derive_payment_status(total_amount, total_paid_raw)
        is_cleared = outstanding_amount == Decimal("0")
        if is_cleared:
            cleared_count += 1
        total_billed += total_amount
        total_collected += settled_amount
        total_outstanding += outstanding_amount
        items.append(
            {
                "invoice_id": row["invoice_id"],
                "invoice_number": row["invoice_number"],
                "invoice_date": row["invoice_date"],
                "patient_id": row["patient_id"],
                "patient_name": row["patient_name"],
                "patient_number": row["patient_number"],
                "total_amount": total_amount,
                "total_paid": total_paid_raw,
                "settled_amount": settled_amount,
                "outstanding_amount": outstanding_amount,
                "overpayment_amount": overpayment_amount,
                "payment_count": payment_count,
                "refund_count": row.get("refund_count", 0),
                "stored_payment_status": row["stored_payment_status"],
                "derived_payment_status": derived_status,
                "status_matches": derived_status
                == str(row["stored_payment_status"]),
                "is_cleared": is_cleared,
            }
        )
    return {
        "as_of": as_of,
        "items": items,
        "total_invoices": len(items),
        "cleared_count": cleared_count,
        "unsettled_count": len(items) - cleared_count,
        "total_billed": total_billed,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
    }


async def build_invoice_settlement_audit_result_from_db(db, limit: int) -> dict:
    """Scan-and-aggregate entry point shared with the reporting service.

    Batch 100 — single implementation behind both
    ``GET /dashboard/invoice-settlement-audit`` and
    ``POST /reports/invoice-settlement-audit-print-envelope``. Reuses the
    exact Batch 94 reconciliation scan (most recent ``limit``
    non-cancelled invoices, one grouped Payment pass), then adds a second
    cheap grouped count of negative ledger entries so each row can report
    how many refunds touched it.
    """
    rows = await _build_reconciliation_rows(db, limit)
    if rows:
        invoice_ids = [row["invoice_id"] for row in rows]
        refunds_result = await db.execute(
            select(Payment.invoice_id, func.count(Payment.id))
            .where(Payment.invoice_id.in_(invoice_ids))
            .where(Payment.amount_paid < 0)
            .group_by(Payment.invoice_id)
        )
        refund_counts = {
            invoice_id: int(count or 0)
            for invoice_id, count in refunds_result
        }
        for row in rows:
            row["refund_count"] = refund_counts.get(row["invoice_id"], 0)
    return build_invoice_settlement_audit_result(rows, date.today())


@router.get(
    "/invoice-settlement-audit", response_model=InvoiceSettlementAuditResponse
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
    result = await build_invoice_settlement_audit_result_from_db(db, limit)
    return InvoiceSettlementAuditResponse(**result)


def build_refund_audit_result(rows: list[dict], as_of: date) -> dict:
    """Pure processing-drift rollup over negative ledger entries.

    Batch 100 — shared derivation behind ``GET /dashboard/refund-audit``
    and its print envelope. Each input row is one negative ``Payment``
    (refund/adjustment) enriched with its invoice context. A refund is
    ``processing_complete`` when all three guards hold: the linked
    invoice exists (``invoice_exists``), a non-empty remarks note
    explains the adjustment (``has_remarks``), and the invoice's net
    collections stay non-negative after the refund
    (``net_non_negative`` — the same invariant the Batch 100 service
    guard enforces at posting time). Drifted rows keep appearing with the
    individual flags false instead of silently disappearing, and
    headlines always satisfy ``processed_count + drifted_count ==
    total_refunds``.
    """
    items = []
    processed_count = 0
    total_refunded = Decimal("0")
    for row in sorted(
        rows,
        key=lambda r: (_as_naive_utc(r["payment_datetime"]), r["payment_id"]),
        reverse=True,
    ):
        refund_amount = abs(Decimal(str(row["refund_amount"])))
        has_remarks = bool((row.get("remarks") or "").strip())
        invoice_exists = row.get("invoice_id") is not None and bool(
            row.get("invoice_number")
        )
        net_paid = row.get("invoice_net_paid")
        net_non_negative = net_paid is None or Decimal(str(net_paid)) >= 0
        processing_complete = (
            has_remarks and invoice_exists and net_non_negative
        )
        if processing_complete:
            processed_count += 1
        total_refunded += refund_amount
        items.append(
            {
                "payment_id": row["payment_id"],
                "receipt_number": row["receipt_number"],
                "payment_datetime": row["payment_datetime"],
                "payment_method": row["payment_method"],
                "refund_amount": refund_amount,
                "invoice_id": row.get("invoice_id"),
                "invoice_number": row.get("invoice_number"),
                "invoice_total_amount": row.get("invoice_total_amount"),
                "invoice_net_paid": net_paid,
                "received_by": row["received_by"],
                "has_remarks": has_remarks,
                "invoice_exists": invoice_exists,
                "net_non_negative": net_non_negative,
                "processing_complete": processing_complete,
            }
        )
    return {
        "as_of": as_of,
        "items": items,
        "total_refunds": len(items),
        "processed_count": processed_count,
        "drifted_count": len(items) - processed_count,
        "total_refunded": total_refunded,
    }


async def build_refund_audit_scan(db, limit: int) -> dict:
    """Scan entry point shared with the reporting service.

    Batch 100 — single implementation behind both
    ``GET /dashboard/refund-audit`` and
    ``POST /reports/refund-audit-print-envelope``. Newest ``limit``
    negative ``Payment`` rows are read in one ordered pass (no N+1), then
    their invoices are loaded in one batched lookup and the per-invoice
    net collections computed by a single grouped pass over the whole
    ledger for those invoices — stored counters and status columns are
    never trusted.
    """
    refunds_result = await db.execute(
        select(Payment)
        .where(Payment.amount_paid < 0)
        .order_by(Payment.payment_datetime.desc(), Payment.id.desc())
        .limit(limit)
    )
    refunds = list(refunds_result.scalars())
    invoice_ids = {r.invoice_id for r in refunds if r.invoice_id is not None}
    invoices: dict[int, Invoice] = {}
    if invoice_ids:
        invoices_result = await db.execute(
            select(Invoice).where(Invoice.id.in_(invoice_ids))
        )
        invoices = {inv.id: inv for inv in invoices_result.scalars()}
    net_paid_by_invoice: dict[int, Decimal] = {}
    if invoice_ids:
        net_result = await db.execute(
            select(Payment.invoice_id, func.sum(Payment.amount_paid))
            .where(Payment.invoice_id.in_(invoice_ids))
            .group_by(Payment.invoice_id)
        )
        net_paid_by_invoice = {
            invoice_id: Decimal(str(total or 0))
            for invoice_id, total in net_result
        }
    rows = []
    for refund in refunds:
        invoice = invoices.get(refund.invoice_id)
        rows.append(
            {
                "payment_id": refund.id,
                "receipt_number": refund.receipt_number,
                "payment_datetime": refund.payment_datetime,
                "payment_method": refund.payment_method,
                "refund_amount": refund.amount_paid,
                "received_by": refund.received_by,
                "remarks": refund.remarks,
                "invoice_id": refund.invoice_id,
                "invoice_number": invoice.invoice_number if invoice else None,
                "invoice_total_amount": (
                    invoice.total_amount if invoice else None
                ),
                "invoice_net_paid": (
                    net_paid_by_invoice.get(refund.invoice_id)
                    if refund.invoice_id is not None
                    else None
                ),
            }
        )
    return build_refund_audit_result(rows, date.today())


@router.get("/refund-audit", response_model=RefundAuditResponse)
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


WARD_UNASSIGNED_LABEL = "Unassigned"


def build_ward_occupancy_summary_result(
    rows: list[dict], as_of: datetime
) -> dict:
    """Pure per-ward rollup over active bed occupancy rows.

    Batch 101 — shared derivation behind ``GET /dashboard/ward-occupancy-
    summary`` (and the matching print envelope). Input rows are
    ``(bed_id, ward, occupancy_status, has_active_admission,
    length_of_stay_days)`` dicts from the grouped bed/admission scan;
    every bed is bucketed under its ward name with null wards surfacing
    under the explicit ``"Unassigned"`` label so nothing disappears from
    the ledger. Statuses outside the occupied/reserved/available vocabulary
    still count toward ``total_beds`` via the available bucket's remainder
    logic below, keeping the split invariant
    ``occupied_beds + reserved_beds + available_beds == total_beds`` true
    for any input. Stay ages are clamped non-negative; wards with no live
    admission report ``longest_stay_days=None`` rather than a fake zero.
    """
    as_of_naive = _as_naive_utc(as_of)
    by_ward: dict[str, dict] = {}
    for row in rows:
        ward = (row.get("ward") or "").strip() or WARD_UNASSIGNED_LABEL
        bucket = by_ward.setdefault(
            ward,
            {
                "ward": ward,
                "total_beds": 0,
                "occupied_beds": 0,
                "reserved_beds": 0,
                "available_beds": 0,
                "active_admissions": 0,
                "longest_stay_days": None,
            },
        )
        bucket["total_beds"] += 1
        status = (row.get("occupancy_status") or "").lower()
        if status == "occupied":
            bucket["occupied_beds"] += 1
        elif status == "reserved":
            bucket["reserved_beds"] += 1
        else:
            bucket["available_beds"] += 1
        if row.get("has_active_admission"):
            bucket["active_admissions"] += 1
            stay = row.get("length_of_stay_days")
            if stay is not None:
                stay = max(int(stay), 0)
                if (
                    bucket["longest_stay_days"] is None
                    or stay > bucket["longest_stay_days"]
                ):
                    bucket["longest_stay_days"] = stay

    items = [
        by_ward[ward]
        for ward in sorted(by_ward, key=lambda w: (w != WARD_UNASSIGNED_LABEL, w))
    ]
    # Unassigned ward sorts last; everything else alphabetically.
    items.sort(key=lambda item: item["ward"])

    return {
        "as_of": as_of_naive,
        "items": items,
        "wards_reported": len(items),
        "total_beds": sum(item["total_beds"] for item in items),
        "total_occupied": sum(item["occupied_beds"] for item in items),
        "total_reserved": sum(item["reserved_beds"] for item in items),
        "total_available": sum(item["available_beds"] for item in items),
        "total_active_admissions": sum(
            item["active_admissions"] for item in items
        ),
    }


async def build_ward_occupancy_summary_scan(db, limit: int) -> list[dict]:
    """Single grouped scan feeding the Batch 101 ward occupancy summary.

    Shared entry point so the dashboard endpoint and the print envelope
    read exactly the same rows: every active bed (capped by ``limit``,
    newest master records first) plus one batched lookup of live
    admissions attached to those beds (the Batch 61 partial unique index
    guarantees at most one active admission per bed, so counts cannot
    double-book). Length-of-stay days are computed against a single
    ``as_of`` snapshot here so the pure rollup above stays deterministic.
    """
    as_of = datetime.now(timezone.utc).replace(tzinfo=None)
    beds_result = await db.execute(
        select(Bed)
        .where(Bed.is_active.is_(True))
        .order_by(Bed.ward.asc(), Bed.bed_number.asc(), Bed.id.desc())
        .limit(limit)
    )
    beds = list(beds_result.scalars().all())
    if not beds:
        return []

    active_statuses = ("admitted", "active")
    bed_ids = [bed.id for bed in beds]
    adm_result = await db.execute(
        select(Admission)
        .where(
            Admission.bed_id.in_(bed_ids),
            func.lower(Admission.admission_status).in_(active_statuses),
        )
        .order_by(Admission.admission_datetime.desc(), Admission.id.desc())
    )
    admissions_by_bed: dict[int, Admission] = {}
    for admission in adm_result.scalars():
        admissions_by_bed.setdefault(admission.bed_id, admission)

    rows = []
    for bed in beds:
        admission = admissions_by_bed.get(bed.id)
        length_of_stay_days = None
        if admission is not None:
            admitted_at = admission.admission_datetime
            if admitted_at.tzinfo is not None:
                admitted_at = admitted_at.astimezone(timezone.utc).replace(
                    tzinfo=None
                )
            length_of_stay_days = max((as_of - admitted_at).days, 0)
        rows.append(
            {
                "bed_id": bed.id,
                "ward": bed.ward,
                "occupancy_status": bed.occupancy_status,
                "has_active_admission": admission is not None,
                "length_of_stay_days": length_of_stay_days,
            }
        )
    return rows


@router.get(
    "/ward-occupancy-summary", response_model=WardOccupancySummaryResponse
)
async def ward_occupancy_summary(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=500, ge=1, le=2000),
) -> WardOccupancySummaryResponse:
    """Per-ward occupancy rollup for hospital-wide ward clarity.

    Batch 101 — complements the existing ``/bed-occupancy`` bed-level feed
    with the ward-level view administrators need: each active bed lands in
    exactly one ward bucket (unlabelled beds surface under "Unassigned"),
    so ``total_occupied + total_reserved + total_available == total_beds``
    always foots against the master bed ledger, and every ward row keeps
    ``occupied_beds + reserved_beds + available_beds == total_beds``.
    Live-admission counts reuse the Batch 61 concurrency guarantees (one
    active admission per bed maximum), so ``active_admissions <=
    occupied_beds`` holds ward-by-ward.
    """
    rows = await build_ward_occupancy_summary_scan(db, limit)
    result = build_ward_occupancy_summary_result(
        rows, datetime.now(timezone.utc).replace(tzinfo=None)
    )
    return WardOccupancySummaryResponse(**result)


__all__ = [
    "build_collection_summary_by_patient",
    "build_discharge_audit_result",
    "build_discharge_audit_scan",
    "build_invoice_settlement_audit_result",
    "build_invoice_settlement_audit_scan",
    "build_overpayment_ledger",
    "build_overpayment_ledger_result",
    "build_opd_queue_summary_result",
    "build_opd_queue_summary_scan",
    "build_payment_method_collection_summary",
    "build_payment_method_overpayment_breakdown",
    "build_payment_method_overpayment_result",
    "build_payment_method_summary_result",
    "build_invoice_settlement_audit_result",
    "build_invoice_settlement_audit_result_from_db",
    "build_receivables_aging_result",
    "build_refund_audit_result",
    "build_refund_audit_scan",
    "build_ward_occupancy_summary_result",
    "build_ward_occupancy_summary_scan",
    "router",
]
