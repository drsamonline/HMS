"""Compliance readiness for the NCH duties.

A report rather than a block: a freshly installed hospital has no registration
numbers yet, and refusing every prescription until they are typed in would make the
product unusable on day one. The report says what to fix.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.database import DatabaseSession
from app.dependencies.permissions import require
from app.services import adverse_events, nch_compliance

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get(
    "/adverse-events",
    dependencies=[Depends(require("clinical.read"))],
)
async def list_adverse_events(
    db: DatabaseSession,
    unreported_only: bool = False,
) -> list[dict]:
    """The pharmacovigilance register, newest first."""

    events = await adverse_events.list_events(db, unreported_only=unreported_only)
    return [
        {
            "id": event.id,
            "patient_id": event.patient_id,
            "product_name": event.product_name,
            "event_datetime": event.event_datetime,
            "severity": event.severity,
            "description": event.description,
            "outcome": event.outcome,
            "reported": event.reported,
            "reported_at": event.reported_at,
            "reported_to": event.reported_to,
        }
        for event in events
    ]


@router.get(
    "/nch-readiness",
    dependencies=[Depends(require("audit.read"))],
)
async def nch_readiness(db: DatabaseSession) -> dict:
    """The NCH duties that can be checked from data, and what fails them."""

    return await nch_compliance.readiness(db)


__all__ = ["router"]
