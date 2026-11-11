"""
Recording and reporting adverse events.

Two acts, deliberately separate: recording an event is something a clinician does
in the consulting room, and reporting it is something the hospital does later. The
register keeps both timestamps, because the gap between them is the evidence.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.models.adverse_event import SEVERITIES, AdverseEvent
from app.models.patient import Patient
from app.services import audit


async def record(
    db: AsyncSession,
    *,
    patient_id: int,
    product_name: str,
    event_datetime: datetime,
    severity: str,
    description: str,
    outcome: str | None = None,
    medicine_id: int | None = None,
    recorded_by: int,
) -> AdverseEvent:
    """Record an event. Nothing is reported yet; that is a second act."""

    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise ResourceNotFoundException("Patient not found.")

    if severity not in SEVERITIES:
        raise BusinessRuleException(
            f"Severity must be one of: {', '.join(SEVERITIES)}."
        )
    if not product_name.strip():
        raise BusinessRuleException("The product must be named.")
    if not description.strip():
        raise BusinessRuleException(
            "The event needs a description; a register of unnamed events reports nothing."
        )

    event = AdverseEvent(
        patient_id=patient_id,
        medicine_id=medicine_id,
        product_name=product_name.strip(),
        event_datetime=event_datetime,
        severity=severity,
        description=description.strip(),
        outcome=outcome.strip() if outcome else None,
        reported=False,
        recorded_by=recorded_by,
    )
    db.add(event)
    await db.flush()

    await audit.record(
        db,
        activity="adverse_event.record",
        entity_name="AdverseEvent",
        entity_id=event.id,
        after={
            "patient_id": patient_id,
            "product_name": event.product_name,
            "severity": severity,
        },
    )
    return event


async def mark_reported(
    db: AsyncSession,
    *,
    event_id: int,
    reported_to: str,
    reported_by: int,
    reported_at: datetime | None = None,
) -> AdverseEvent:
    """Note that the event reached the authority.

    Idempotent: reporting twice records the first report and says so, because a
    second date would make the register look like two events.
    """

    event = await db.get(AdverseEvent, event_id)
    if event is None:
        raise ResourceNotFoundException("Adverse event not found.")
    if not reported_to.strip():
        raise BusinessRuleException("Say who the event was reported to.")

    if event.reported:
        return event

    event.reported = True
    event.reported_at = reported_at or datetime.now(UTC)
    event.reported_to = reported_to.strip()
    event.reported_by = reported_by

    await audit.record(
        db,
        activity="adverse_event.report",
        entity_name="AdverseEvent",
        entity_id=event.id,
        before={"reported": False},
        after={"reported": True, "reported_to": event.reported_to},
    )
    await db.flush()
    return event


async def unreported_count(db: AsyncSession) -> int:
    from sqlalchemy import func

    result = await db.execute(
        select(func.count()).select_from(AdverseEvent).where(AdverseEvent.reported.is_(False))
    )
    return result.scalar_one()


async def list_events(
    db: AsyncSession, *, unreported_only: bool = False, limit: int = 100
) -> list[AdverseEvent]:
    query = select(AdverseEvent).order_by(AdverseEvent.event_datetime.desc()).limit(limit)
    if unreported_only:
        query = query.where(AdverseEvent.reported.is_(False))
    return list((await db.execute(query)).scalars().all())


__all__ = ["list_events", "mark_reported", "record", "unreported_count"]
