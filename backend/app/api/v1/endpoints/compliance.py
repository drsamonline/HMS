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
from app.services import nch_compliance

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get(
    "/nch-readiness",
    dependencies=[Depends(require("audit.read"))],
)
async def nch_readiness(db: DatabaseSession) -> dict:
    """The NCH duties that can be checked from data, and what fails them."""

    return await nch_compliance.readiness(db)


__all__ = ["router"]
