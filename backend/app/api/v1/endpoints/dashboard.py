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

Batch 84 — Laboratory Pending-Investigation Continuity: surfaces the
laboratory workload still awaiting results (pending/in_progress orders,
oldest-first) with patient identity enrichment, so outstanding
investigations are actionable from the client dashboard and hand off
into the same clinical workspace as the sibling feeds.
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
from app.models.patient import Patient
from app.models.payment import Payment
from app.schemas.dashboard import (
    BedOccupancyResponse,
    DueFollowUpsResponse,
    OutstandingInvoicesResponse,
    PendingInvestigationsResponse,
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
    limit: int = Query(default=100, ge=1, le=200),
) -> PendingInvestigationsResponse:
    """Outstanding laboratory investigations awaiting results.

    Built on the Batch 66 result workflow (pending -> in_progress on
    verification, completed on release): every order still in the pending or
    in-progress state is workload that has not reached the clinician yet. The
    feed is oldest-first with per-row age so the backlog is prioritised, and
    each row is enriched with patient identity via a batched lookup (no N+1)
    so orders can be chased directly from the dashboard. Cancelled and
    completed orders never surface.
    """
    outstanding_statuses = ("pending", "in_progress")
    orders_result = await db.execute(
        select(Investigation)
        .where(
            func.lower(Investigation.investigation_status).in_(outstanding_statuses)
        )
        .order_by(
            Investigation.requested_datetime.asc(),
            Investigation.id.asc(),
        )
        .limit(limit)
    )
    orders = list(orders_result.scalars().all())

    patient_ids = {order.patient_id for order in orders}
    patients: dict[int, Patient] = {}
    if patient_ids:
        result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        patients = {p.id: p for p in result.scalars()}

    as_of = datetime.now(timezone.utc).replace(tzinfo=None)
    pending_count = 0
    in_progress_count = 0
    items = []
    for order in orders:
        status = (order.investigation_status or "").lower()
        if status == "pending":
            pending_count += 1
        else:
            in_progress_count += 1
        requested_at = order.requested_datetime
        if requested_at.tzinfo is not None:
            requested_at = requested_at.astimezone(timezone.utc).replace(tzinfo=None)
        age_hours = max(int((as_of - requested_at).total_seconds() // 3600), 0)
        patient = patients.get(order.patient_id)
        items.append(
            {
                "investigation_id": order.id,
                "investigation_number": order.investigation_number,
                "patient_id": order.patient_id,
                "patient_name": _patient_display_name(patient),
                "patient_number": patient.patient_number if patient else None,
                "investigation_name": order.investigation_name,
                "investigation_status": order.investigation_status,
                "requested_datetime": order.requested_datetime,
                "requested_by": order.requested_by,
                "visit_id": order.visit_id,
                "admission_id": order.admission_id,
                "age_hours": age_hours,
            }
        )

    return PendingInvestigationsResponse(
        as_of=datetime.now(timezone.utc),
        items=items,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
    )


__all__ = ["router"]
