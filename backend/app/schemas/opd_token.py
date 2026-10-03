"""
HHMS OPD Token Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class OPDTokenCreate(BaseSchema):
    """Request to generate an OPD token."""

    visit_id: int = Field(gt=0)
    queue_date: date


class OPDTokenUpdate(BaseSchema):
    """Update OPD queue status."""

    queue_status: str = Field(
        min_length=1,
        max_length=20,
    )
    called_at: datetime | None = None
    completed_at: datetime | None = None


class OPDTokenRead(BaseSchema):
    """OPD token response."""

    id: int
    visit_id: int
    token_number: int
    queue_date: date
    queue_status: str
    generated_at: datetime
    called_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "OPDTokenCreate",
    "OPDTokenUpdate",
    "OPDTokenRead",
]