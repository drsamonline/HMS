"""
HHMS Visit Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class VisitBase(BaseSchema):
    patient_id: int = Field(gt=0)
    visit_type: str = Field(min_length=1, max_length=20)
    visit_datetime: datetime
    chief_complaint: str | None = None
    consultation_status: str = Field(
        default="registered",
        min_length=1,
        max_length=20,
    )
    consulting_doctor_id: int = Field(gt=0)
    remarks: str | None = None


class VisitCreate(VisitBase):
    """Create a clinical visit."""


class VisitUpdate(BaseSchema):
    """Partially update a clinical visit."""

    visit_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    visit_datetime: datetime | None = None
    chief_complaint: str | None = None
    consultation_status: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    consulting_doctor_id: int | None = Field(
        default=None,
        gt=0,
    )
    remarks: str | None = None


class VisitRead(VisitBase):
    """Visit response."""

    id: int
    visit_number: str
    created_at: datetime
    updated_at: datetime


__all__ = [
    "VisitBase",
    "VisitCreate",
    "VisitUpdate",
    "VisitRead",
]