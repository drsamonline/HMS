"""The institution's statutory registrations.

A clinic asks three questions and rarely has answers: what do we hold, when does it
expire, and what is missing. This answers all three, and refuses to decide what the law
requires of a particular premises - that depends on the state.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.exceptions import BusinessRuleException
from app.dependencies.database import DatabaseSession
from app.dependencies.permissions import require
from app.services import institute_registrations

router = APIRouter(prefix="/institute", tags=["Institute"])


class RegistrationWrite(BaseModel):
    number: str
    authority: str | None = None
    issued_on: datetime | None = None
    valid_until: datetime | None = None
    applies: bool = True
    notes: str | None = None


@router.get(
    "/registrations",
    dependencies=[Depends(require("settings.read"))],
)
async def list_registrations(db: DatabaseSession) -> dict:
    """Every known registration kind, what is held, and what needs attention."""

    return await institute_registrations.readiness(db)


@router.put(
    "/registrations/{kind}",
    dependencies=[Depends(require("settings.write"))],
)
async def record_registration(
    kind: str, payload: RegistrationWrite, db: DatabaseSession
) -> dict:
    """Record or update one registration."""

    try:
        await institute_registrations.upsert(
            db,
            kind=kind,
            number=payload.number,
            authority=payload.authority,
            issued_on=payload.issued_on,
            valid_until=payload.valid_until,
            applies=payload.applies,
            notes=payload.notes,
        )
    except BusinessRuleException as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    await db.commit()
    return await institute_registrations.readiness(db)


__all__ = ["router"]
