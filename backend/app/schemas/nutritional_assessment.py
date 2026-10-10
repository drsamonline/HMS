"""HHMS Nutritional Assessment schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class NutritionalAssessmentCreate(BaseSchema):
    admission_id: int
    assessment_datetime: datetime
    appetite: str | None = None
    dietary_pattern: str | None = None
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    bmi: Decimal | None = None
    risk_level: str | None = None
    nutritional_findings: str | None = None
    recommendations: str | None = None
    notes: str | None = None

    recorded_by: int = Field(gt=0)

class NutritionalAssessmentUpdate(BaseSchema):
    assessment_datetime: datetime | None = None
    appetite: str | None = None
    dietary_pattern: str | None = None
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    bmi: Decimal | None = None
    risk_level: str | None = None
    nutritional_findings: str | None = None
    recommendations: str | None = None
    notes: str | None = None


class NutritionalAssessmentRead(BaseSchema):
    id: int
    admission_id: int
    assessment_datetime: datetime
    appetite: str | None
    dietary_pattern: str | None
    weight_kg: Decimal | None
    height_cm: Decimal | None
    bmi: Decimal | None
    risk_level: str | None
    nutritional_findings: str | None
    recommendations: str | None
    notes: str | None
    recorded_by: int
    created_at: datetime
    updated_at: datetime


__all__ = ["NutritionalAssessmentCreate", "NutritionalAssessmentUpdate", "NutritionalAssessmentRead"]
