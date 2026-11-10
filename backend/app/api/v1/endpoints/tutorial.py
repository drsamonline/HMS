"""The guided first run, as the client needs it.

No permission guard beyond a login: everybody who uses the software has a first day,
including the administrator.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter

from app.dependencies.database import DatabaseSession
from app.services import tutorial

router = APIRouter(prefix="/tutorial", tags=["Tutorial"])


@router.get("")
async def get_tutorial(db: DatabaseSession) -> dict:
    """The five steps, and how far this hospital has got."""

    return await tutorial.progress(db)


__all__ = ["router"]
