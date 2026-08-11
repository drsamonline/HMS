"""
HHMS Prescription Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class PrescriptionItemCreate(BaseSchema):
    """Medicine prescribed within a prescription."""

    medicine_id: int = Field(gt=0)
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=1, max_length=100)
    duration_days: int | None = Field(
        default=None,
        ge=1,
    )
    instructions: str | None = None
    quantity: Decimal = Field(gt=0)


class PrescriptionItemRead(PrescriptionItemCreate):
    """Prescription medicine line response."""

    id: int
    prescription_id: int
    created_at: datetime
    updated_at: datetime


class PrescriptionCreate(BaseSchema):
    """Create a prescription with its medicine lines."""

    visit_id: int = Field(gt=0)
    prescribed_by: int = Field(gt=0)
    prescription_datetime: datetime
    diagnosis: str | None = None
    clinical_notes: str | None = None
    treatment_plan: str | None = None
    items: list[PrescriptionItemCreate] = Field(
        min_length=1,
    )


class PrescriptionUpdate(BaseSchema):
    """Update prescription header information."""

    diagnosis: str | None = None
    clinical_notes: str | None = None
    treatment_plan: str | None = None
    printed_at: datetime | None = None


class PrescriptionRead(BaseSchema):
    """Complete prescription response."""

    id: int
    visit_id: int
    prescription_number: str
    diagnosis: str | None
    clinical_notes: str | None
    treatment_plan: str | None
    prescribed_by: int
    prescription_datetime: datetime
    printed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[PrescriptionItemRead]


__all__ = [
    "PrescriptionCreate",
    "PrescriptionUpdate",
    "PrescriptionRead",
    "PrescriptionItemCreate",
    "PrescriptionItemRead",
]