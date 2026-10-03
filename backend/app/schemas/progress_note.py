"""HHMS Clinical Progress Note schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class ProgressNoteCreate(BaseSchema):
    admission_id: int
    note_datetime: datetime
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    clinical_notes: str | None = None
    remarks: str | None = None

    recorded_by: int = Field(gt=0)

class ProgressNoteUpdate(BaseSchema):
    note_datetime: datetime | None = None
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    clinical_notes: str | None = None
    remarks: str | None = None


class ProgressNoteRead(BaseSchema):
    id: int
    admission_id: int
    note_datetime: datetime
    subjective: str | None
    objective: str | None
    assessment: str | None
    plan: str | None
    clinical_notes: str | None
    remarks: str | None
    recorded_by: int
    created_at: datetime
    updated_at: datetime


__all__ = ["ProgressNoteCreate", "ProgressNoteUpdate", "ProgressNoteRead"]
