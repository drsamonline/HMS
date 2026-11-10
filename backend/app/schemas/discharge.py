"""
HHMS Discharge Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


DischargeStatus = Literal[
    "discharged",
    "cancelled",
]

#: How the episode ended. ``discharge_status`` says whether this record is valid;
#: this says what happened to the patient, which is what NABH asks for.
DischargeOutcome = Literal[
    "routine",
    "expired",
    "against_advice",
    "transferred",
]


class DischargeCreate(BaseSchema):
    admission_id: int = Field(gt=0)

    discharge_datetime: datetime

    discharge_summary: str | None = None

    discharge_outcome: DischargeOutcome | None = None
    discharge_status: DischargeStatus = (
        "discharged"
    )

    discharged_by: int = Field(gt=0)

    remarks: str | None = None


class DischargeRead(BaseSchema):
    id: int
    admission_id: int
    discharge_number: str
    discharge_datetime: datetime
    discharge_summary: str | None
    discharge_status: str
    discharged_by: int
    remarks: str | None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "DischargeOutcome",
    "DischargeStatus",
    "DischargeCreate",
    "DischargeRead",
]