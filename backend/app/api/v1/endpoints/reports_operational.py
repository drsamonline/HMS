"""
Operational dashboards: What the hospital is doing right now.

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

router = APIRouter(prefix="/dashboard", tags=["Operational dashboards"])



@router.get("/bed-occupancy", response_model=BedOccupancyResponse, dependencies=[Depends(require("reports.operational"))])
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


@router.get("/opd-queue-summary", response_model=OPDQueueSummaryResponse, dependencies=[Depends(require("reports.operational"))])
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


@router.get(
    "/ward-occupancy-summary", response_model=WardOccupancySummaryResponse,
    dependencies=[Depends(require("reports.operational"))],
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


# ---------------------------------------------------------------------------
# Batch 102 — Investigation Billing Reconciliation
# ---------------------------------------------------------------------------

