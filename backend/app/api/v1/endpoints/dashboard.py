"""HHMS clinician dashboard endpoints.

Batch 79 — Due Follow-up Workflow Continuity: turns the Batch 78 due-window
service query into a workflow-ready dashboard feed by joining each due
follow-up to its patient and case identity, so clinicians can act on today's
follow-up list directly from the client dashboard.

Batch 82 — Outstanding Billing Continuity: surfaces the billing service's
oldest-first outstanding-invoice feed (derived balances over live payments)
as an administrative receivables panel with patient identity enrichment.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Query

from sqlalchemy import func, select

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.models.case_record import CaseRecord
from app.models.patient import Patient
from app.models.payment import Payment
from app.schemas.dashboard import (
    DueFollowUpsResponse,
    OutstandingInvoicesResponse,
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


__all__ = ["router"]
