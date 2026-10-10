"""HHMS Diet Chart schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class DietChartCreate(BaseSchema):
    admission_id: int
    chart_date: datetime
    diet_type: str | None = None
    breakfast: str | None = None
    mid_morning: str | None = None
    lunch: str | None = None
    evening: str | None = None
    dinner: str | None = None
    special_instructions: str | None = None
    remarks: str | None = None

    recorded_by: int = Field(gt=0)

class DietChartUpdate(BaseSchema):
    chart_date: datetime | None = None
    diet_type: str | None = None
    breakfast: str | None = None
    mid_morning: str | None = None
    lunch: str | None = None
    evening: str | None = None
    dinner: str | None = None
    special_instructions: str | None = None
    remarks: str | None = None


class DietChartRead(BaseSchema):
    id: int
    admission_id: int
    chart_date: datetime
    diet_type: str | None
    breakfast: str | None
    mid_morning: str | None
    lunch: str | None
    evening: str | None
    dinner: str | None
    special_instructions: str | None
    remarks: str | None
    recorded_by: int
    created_at: datetime
    updated_at: datetime


__all__ = ["DietChartCreate", "DietChartUpdate", "DietChartRead"]
