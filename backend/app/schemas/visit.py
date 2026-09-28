"""
HHMS Visit Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


VisitCaseType = Literal["new", "old"]


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
    department_id: UUID | None = None
    service_id: UUID | None = None
    case_type: VisitCaseType | None = None
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
    department_id: UUID | None = None
    service_id: UUID | None = None
    case_type: VisitCaseType | None = None
    consulting_doctor_id: int | None = Field(
        default=None,
        gt=0,
    )
    remarks: str | None = None


class VisitRead(VisitBase):
    """Visit response."""

    id: int
    visit_number: str
    visit_year: int = 0
    storage_tier: str = "live"
    is_current_year: bool = True
    created_at: datetime
    updated_at: datetime


__all__ = [
    "VisitBase",
    "VisitCreate",
    "VisitUpdate",
    "VisitRead",
]