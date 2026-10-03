"""HHMS Pain Assessment schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class PainAssessmentCreate(BaseSchema):
    admission_id: int
    assessment_datetime: datetime
    pain_present: bool | None = None
    pain_score: int | None = Field(default=None, ge=0, le=10)
    site: str | None = None
    character: str | None = None
    aggravating_factors: str | None = None
    relieving_factors: str | None = None
    intervention: str | None = None
    reassessment_score: int | None = Field(default=None, ge=0, le=10)
    notes: str | None = None

    recorded_by: int = Field(gt=0)

class PainAssessmentUpdate(BaseSchema):
    assessment_datetime: datetime | None = None
    pain_present: bool | None = None
    pain_score: int | None = None
    site: str | None = None
    character: str | None = None
    aggravating_factors: str | None = None
    relieving_factors: str | None = None
    intervention: str | None = None
    reassessment_score: int | None = None
    notes: str | None = None


class PainAssessmentRead(BaseSchema):
    id: int
    admission_id: int
    assessment_datetime: datetime
    pain_present: bool | None
    pain_score: int | None
    site: str | None
    character: str | None
    aggravating_factors: str | None
    relieving_factors: str | None
    intervention: str | None
    reassessment_score: int | None
    notes: str | None
    recorded_by: int
    created_at: datetime
    updated_at: datetime


__all__ = ["PainAssessmentCreate", "PainAssessmentUpdate", "PainAssessmentRead"]
