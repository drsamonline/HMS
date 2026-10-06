"""HHMS Homoeopathic Follow-up schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


Status = Literal["better", "same", "worse"]
RemedyResponse = Literal["good", "partial", "none", "aggravation", "unclear"]
Decision = Literal["wait", "repeat", "change_remedy", "stop_reassess"]


class FollowUpCreate(BaseSchema):
    case_record_id: int = Field(gt=0)
    patient_id: int = Field(gt=0)
    visit_id: int | None = Field(default=None, gt=0)
    followup_datetime: datetime
    general_status: Status | None = None
    mental_status: Status | None = None
    particular_status: Status | None = None
    remedy_response: RemedyResponse | None = None
    decision: Decision | None = None
    new_symptoms: str | None = None
    old_symptoms: str | None = None
    clinical_assessment: str | None = None
    notes: str | None = None
    previous_prescription_id: int | None = Field(default=None, gt=0)
    next_prescription_id: int | None = Field(default=None, gt=0)
    next_followup_datetime: datetime | None = None


class FollowUpUpdate(BaseSchema):
    followup_datetime: datetime | None = None
    general_status: Status | None = None
    mental_status: Status | None = None
    particular_status: Status | None = None
    remedy_response: RemedyResponse | None = None
    decision: Decision | None = None
    new_symptoms: str | None = None
    old_symptoms: str | None = None
    clinical_assessment: str | None = None
    notes: str | None = None
    previous_prescription_id: int | None = Field(default=None, gt=0)
    next_prescription_id: int | None = Field(default=None, gt=0)
    next_followup_datetime: datetime | None = None


class FollowUpRead(FollowUpCreate):
    id: int
    recorded_by: int
    created_at: datetime
    updated_at: datetime


__all__ = [
    "Status",
    "RemedyResponse",
    "Decision",
    "FollowUpCreate",
    "FollowUpUpdate",
    "FollowUpRead",
]
