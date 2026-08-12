"""HHMS IPD Assessment schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class IPDAssessmentCreate(BaseSchema):
    admission_id: int
    assessment_datetime: datetime
    clinical_summary: str | None = None
    presenting_complaints: str | None = None
    history_present_illness: str | None = None
    general_examination: str | None = None
    systemic_examination: str | None = None
    initial_assessment: str | None = None
    remarks: str | None = None

    recorded_by: int = Field(gt=0)

class IPDAssessmentUpdate(BaseSchema):
    assessment_datetime: datetime | None = None
    clinical_summary: str | None = None
    presenting_complaints: str | None = None
    history_present_illness: str | None = None
    general_examination: str | None = None
    systemic_examination: str | None = None
    initial_assessment: str | None = None
    remarks: str | None = None


class IPDAssessmentRead(BaseSchema):
    id: int
    admission_id: int
    assessment_datetime: datetime
    clinical_summary: str | None
    presenting_complaints: str | None
    history_present_illness: str | None
    general_examination: str | None
    systemic_examination: str | None
    initial_assessment: str | None
    remarks: str | None
    recorded_by: int
    created_at: datetime
    updated_at: datetime


__all__ = ["IPDAssessmentCreate", "IPDAssessmentUpdate", "IPDAssessmentRead"]
