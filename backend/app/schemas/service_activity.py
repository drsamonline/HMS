"""Schemas for the generic departmental activity ledger."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field
from app.schemas.base import BaseSchema


class ServiceActivityCreate(BaseSchema):
    patient_id: int = Field(gt=0)
    department_id: UUID
    service_id: UUID
    activity_datetime: datetime
    case_type: str = Field(default="new", pattern="^(new|old)$")
    fulfillment_mode: str | None = Field(default=None, max_length=20)
    source_type: str | None = Field(default=None, max_length=30)
    source_id: int | None = Field(default=None, gt=0)
    status: str = Field(default="completed", min_length=1, max_length=20)
    remarks: str | None = None


class ServiceActivityRead(ServiceActivityCreate):
    id: int


__all__ = ["ServiceActivityCreate", "ServiceActivityRead"]
