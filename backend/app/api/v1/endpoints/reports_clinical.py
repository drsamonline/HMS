"""
Clinical follow-through: What is outstanding for a patient.

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

router = APIRouter(prefix="/dashboard", tags=["Clinical follow-through"])



@router.get("/due-followups", response_model=DueFollowUpsResponse, dependencies=[Depends(require("reports.clinical"))])
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


@router.get("/pending-investigations", response_model=PendingInvestigationsResponse, dependencies=[Depends(require("reports.clinical"))])
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
@router.get("/discharge-audit", response_model=DischargeAuditResponse, dependencies=[Depends(require("reports.clinical"))])
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


