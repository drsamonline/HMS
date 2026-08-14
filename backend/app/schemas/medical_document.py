"""HHMS Medical Document schemas."""
from __future__ import annotations
from datetime import datetime
from pydantic import Field
from app.schemas.base import BaseSchema

class MedicalDocumentCreate(BaseSchema):
    patient_id: int = Field(gt=0)
    visit_id: int | None = Field(default=None, gt=0)
    admission_id: int | None = Field(default=None, gt=0)
    document_number: str = Field(min_length=1, max_length=20)
    document_type: str = Field(min_length=1, max_length=50)
    document_title: str = Field(min_length=1, max_length=200)
    file_name: str | None = Field(default=None, max_length=255)
    file_path: str | None = Field(default=None, max_length=500)
    document_date: datetime
    remarks: str | None = None

class MedicalDocumentUpdate(BaseSchema):
    document_type: str | None = Field(default=None, min_length=1, max_length=50)
    document_title: str | None = Field(default=None, min_length=1, max_length=200)
    file_name: str | None = Field(default=None, max_length=255)
    file_path: str | None = Field(default=None, max_length=500)
    document_date: datetime | None = None
    remarks: str | None = None

class MedicalDocumentRead(BaseSchema):
    id: int
    patient_id: int
    visit_id: int | None
    admission_id: int | None
    document_number: str
    document_type: str
    document_title: str
    file_name: str | None
    file_path: str | None
    document_date: datetime
    uploaded_by: int
    remarks: str | None
    created_at: datetime
    updated_at: datetime

__all__ = ["MedicalDocumentCreate", "MedicalDocumentUpdate", "MedicalDocumentRead"]
