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
from app.models.investigation import Investigation
from app.models.invoice import Invoice
from app.models.patient import Patient
from app.models.payment import Payment
from app.schemas.dashboard import (
    BedOccupancyResponse,
    DueFollowUpsResponse,
    InvoicePaymentReconciliationResponse,
    InvoiceReceiptContinuityResponse,
    OutstandingInvoicesResponse,
    PendingInvestigationsResponse,
    ReceiptNumberingContinuityResponse,
    ReceivablesAgingResponse,
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
    Patient enrichment is batched (no N+1).
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

    return ReceivablesAgingResponse(
        as_of=as_of,
        buckets=buckets,
        items=items,
        invoice_count=len(items),
        total_outstanding=total_outstanding,
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


@router.get("/invoice-receipt-continuity", response_model=InvoiceReceiptContinuityResponse)
async def invoice_receipt_continuity(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> InvoiceReceiptContinuityResponse:
    """Audit invoice-to-receipt numbering continuity on live billing data.

    Batch 87 — reporting/printing integration feed. Scans the most recent
    invoices and, for each, checks the receipts recorded against it:

    * ``missing`` — an invoice carries payments whose receipt rows no longer
      link back (or, with amount paid but no receipt, the receipt book is
      short one entry);
    * ``duplicate`` — the same receipt number appears more than once within
      an invoice's receipts;
    * ``sequence_break`` — the numeric suffixes of an invoice's receipts skip
      at least one value between first and last.

    The audit never trusts stored counters: receipt counts come from a single
    grouped query over the Payment table (no N+1), and every aggregate sums
    back to ``invoices_checked`` so printed continuity reports reconcile.
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

    # Single grouped pass over receipts for all scanned invoices (no N+1).
    # ``paid_by_invoice`` uses the same live-payment derivation as Batch 82.
    receipts_by_invoice: dict[int, list[tuple[str,]]] = {}
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

    return InvoiceReceiptContinuityResponse(
        as_of=datetime.now(timezone.utc),
        invoices_checked=len(invoices),
        invoices_with_receipts=invoices_with_receipts,
        invoices_missing_receipts=invoices_missing_receipts,
        duplicate_receipt_count=duplicate_receipt_count,
        sequence_break_count=sequence_break_count,
        issues=issues,
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

    return ReceiptNumberingContinuityResponse(
        as_of=datetime.now(timezone.utc),
        receipts_checked=len(receipt_numbers),
        series_count=len(series_items),
        clean_series_count=clean_series_count,
        total_gap_count=total_gap_count,
        series=series_items,
    )


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


@router.get("/invoice-payment-reconciliation", response_model=InvoicePaymentReconciliationResponse)
async def invoice_payment_reconciliation(
    db: DatabaseSession,
    _: CurrentUserDependency,
    limit: int = Query(default=200, ge=1, le=500),
) -> InvoicePaymentReconciliationResponse:
    """Reconcile recent invoices against the live Payment ledger.

    Batch 89 — reporting/printing integration feed. Where Batch 82/86 only
    surfaced *outstanding* invoices, this ledger reconciles **every** scanned
    invoice (most recent ``limit`` non-cancelled invoices): payments are
    summed in a single grouped pass over the ``Payment`` table (no N+1,
    stored counters and status columns are never trusted), ``amount_paid`` is
    clamped to the invoice total and ``balance_due`` kept non-negative so the
    invariant ``amount_paid + balance_due == total_amount`` holds on every
    printed row (Batch 68 parity).

    Each row also carries the derived payment status next to the stored one
    (``is_reconciled`` flags drift between the two) plus the number of
    receipts recorded against the invoice, so billing staff can prove
    collection state line-by-line before printing. Headline aggregates sum
    back to ``invoices_checked`` and the totals satisfy
    ``total_billed == total_paid + total_outstanding``.
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
    # invoices (no N+1): per-invoice paid totals and receipt counts.
    paid_by_invoice: dict[int, Decimal] = {}
    receipts_by_invoice: dict[int, int] = {}
    if invoices:
        invoice_ids = [invoice.id for invoice in invoices]
        payments_result = await db.execute(
            select(
                Payment.invoice_id,
                Payment.receipt_number,
                Payment.amount_paid,
            ).where(Payment.invoice_id.in_(invoice_ids))
        )
        for invoice_id, _receipt_number, amount_paid in payments_result:
            paid_by_invoice[invoice_id] = paid_by_invoice.get(
                invoice_id, Decimal("0")
            ) + Decimal(str(amount_paid))
            receipts_by_invoice[invoice_id] = receipts_by_invoice.get(invoice_id, 0) + 1

    items = []
    paid_invoices = 0
    partially_paid_invoices = 0
    unpaid_invoices = 0
    total_billed = Decimal("0")
    total_paid = Decimal("0")
    total_outstanding = Decimal("0")
    for invoice in invoices:
        patient = patients.get(invoice.patient_id)
        amount_paid = min(
            paid_by_invoice.get(invoice.id, Decimal("0")),
            invoice.total_amount,
        )
        balance_due = max(invoice.total_amount - amount_paid, Decimal("0"))
        derived_status = _derive_payment_status(invoice.total_amount, amount_paid)
        if derived_status == "paid":
            paid_invoices += 1
        elif derived_status == "partial":
            partially_paid_invoices += 1
        else:
            unpaid_invoices += 1
        total_billed += invoice.total_amount
        total_paid += amount_paid
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
                "stored_payment_status": invoice.payment_status,
                "derived_payment_status": derived_status,
                "receipt_count": receipts_by_invoice.get(invoice.id, 0),
                "is_reconciled": derived_status == str(invoice.payment_status),
            }
        )

    return InvoicePaymentReconciliationResponse(
        as_of=date.today(),
        invoices_checked=len(items),
        paid_invoices=paid_invoices,
        partially_paid_invoices=partially_paid_invoices,
        unpaid_invoices=unpaid_invoices,
        total_billed=total_billed,
        total_paid=total_paid,
        total_outstanding=total_outstanding,
        items=items,
    )


__all__ = ["router"]
