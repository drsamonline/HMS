"""
HHMS Investigation Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


InvestigationStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "cancelled",
]


class InvestigationCreate(BaseSchema):
    patient_id: int = Field(gt=0)

    visit_id: int | None = Field(
        default=None,
        gt=0,
    )

    admission_id: int | None = Field(
        default=None,
        gt=0,
    )

    investigation_name: str = Field(
        min_length=1,
        max_length=150,
    )

    requested_by: int = Field(gt=0)

    requested_datetime: datetime

    investigation_status: InvestigationStatus = (
        "pending"
    )

    remarks: str | None = None


class InvestigationUpdate(BaseSchema):
    investigation_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    investigation_status: InvestigationStatus | None = None

    remarks: str | None = None


class InvestigationRead(BaseSchema):
    id: int
    patient_id: int
    visit_id: int | None
    admission_id: int | None
    investigation_number: str
    investigation_name: str
    requested_by: int
    requested_datetime: datetime
    investigation_status: str
    remarks: str | None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "InvestigationStatus",
    "InvestigationCreate",
    "InvestigationUpdate",
    "InvestigationRead",
]