"""HHMS Medical Records Department archive schemas."""
from __future__ import annotations
from datetime import datetime
from pydantic import Field
from app.schemas.base import BaseSchema

class ArchiveRecordCreate(BaseSchema):
    patient_file_id: int = Field(gt=0)
    archive_date: datetime | None = None
    archive_location: str | None = Field(default=None, max_length=200)
    box_no: str | None = Field(default=None, max_length=50)
    retention_period: str | None = Field(default=None, max_length=100)
    status: str = Field(default="pending", min_length=1, max_length=30)

class ArchiveRecordUpdate(BaseSchema):
    archive_date: datetime | None = None
    archive_location: str | None = Field(default=None, max_length=200)
    box_no: str | None = Field(default=None, max_length=50)
    retention_period: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, min_length=1, max_length=30)

class ArchiveRecordRead(BaseSchema):
    id: int
    patient_file_id: int
    archive_date: datetime | None
    archive_location: str | None
    box_no: str | None
    retention_period: str | None
    status: str
    created_at: datetime
    updated_at: datetime

__all__ = ["ArchiveRecordCreate", "ArchiveRecordUpdate", "ArchiveRecordRead"]
