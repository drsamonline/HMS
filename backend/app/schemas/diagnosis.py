"""HHMS Diagnosis schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


DiagnosisType = Literal[
    "clinical",
    "provisional",
    "differential",
    "confirmed",
    "other",
]


class DiagnosisCreate(BaseSchema):
    case_record_id: int = Field(gt=0)
    patient_id: int = Field(gt=0)
    visit_id: int | None = Field(default=None, gt=0)
    diagnosis_name: str = Field(min_length=1, max_length=200)
    diagnosis_type: DiagnosisType = "clinical"
    icd11_code: str | None = Field(default=None, max_length=30)
    icd11_title: str | None = Field(default=None, max_length=300)
    icd11_uri: str | None = Field(default=None, max_length=500)
    icd11_release: str | None = Field(default=None, max_length=20)
    is_primary: bool = False
    notes: str | None = None


class DiagnosisUpdate(BaseSchema):
    diagnosis_name: str | None = Field(default=None, min_length=1, max_length=200)
    diagnosis_type: DiagnosisType | None = None
    icd11_code: str | None = Field(default=None, max_length=30)
    icd11_title: str | None = Field(default=None, max_length=300)
    icd11_uri: str | None = Field(default=None, max_length=500)
    icd11_release: str | None = Field(default=None, max_length=20)
    is_primary: bool | None = None
    notes: str | None = None


class DiagnosisRead(DiagnosisCreate):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime


__all__ = [
    "DiagnosisType",
    "DiagnosisCreate",
    "DiagnosisUpdate",
    "DiagnosisRead",
]
