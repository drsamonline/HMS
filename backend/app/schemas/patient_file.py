"""HHMS Medical Records Department patient-file schemas."""
from __future__ import annotations
from datetime import datetime
from pydantic import Field
from app.schemas.base import BaseSchema

class PatientFileCreate(BaseSchema):
    patient_id: int = Field(gt=0)
    file_no: str = Field(min_length=1, max_length=50)
    file_type: str = Field(min_length=1, max_length=50)
    location: str | None = Field(default=None, max_length=200)
    shelf_no: str | None = Field(default=None, max_length=50)
    rack_no: str | None = Field(default=None, max_length=50)
    status: str = Field(default="active", min_length=1, max_length=30)

class PatientFileUpdate(BaseSchema):
    file_type: str | None = Field(default=None, min_length=1, max_length=50)
    location: str | None = Field(default=None, max_length=200)
    shelf_no: str | None = Field(default=None, max_length=50)
    rack_no: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, min_length=1, max_length=30)

class PatientFileRead(BaseSchema):
    id: int
    patient_id: int
    file_no: str
    file_type: str
    location: str | None
    shelf_no: str | None
    rack_no: str | None
    status: str
    created_at: datetime
    updated_at: datetime

__all__ = ["PatientFileCreate", "PatientFileUpdate", "PatientFileRead"]
