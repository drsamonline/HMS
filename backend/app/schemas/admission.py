"""
HHMS Admission Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class AdmissionCreate(BaseSchema):
    patient_id: int = Field(gt=0)
    admission_datetime: datetime
    bed_id: int = Field(gt=0)
    admitted_by: int = Field(gt=0)
    admission_reason: str | None = None
    admission_status: str = Field(
        default="admitted",
        min_length=1,
        max_length=20,
    )
    remarks: str | None = None


class AdmissionUpdate(BaseSchema):
    admission_reason: str | None = None
    admission_status: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    remarks: str | None = None


class AdmissionRead(BaseSchema):
    id: int
    patient_id: int
    admission_number: str
    admission_datetime: datetime
    bed_id: int
    admitted_by: int
    admission_reason: str | None
    admission_status: str
    remarks: str | None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "AdmissionCreate",
    "AdmissionUpdate",
    "AdmissionRead",
]