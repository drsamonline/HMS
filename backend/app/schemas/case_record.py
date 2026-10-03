"""HHMS Homoeopathic Case Record schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema


CaseStatus = Literal["draft", "active", "closed"]


class CaseRecordCreate(BaseSchema):
    patient_id: int = Field(gt=0)
    visit_id: int | None = Field(default=None, gt=0)
    admission_id: int | None = Field(default=None, gt=0)
    case_status: CaseStatus = "draft"
    case_family_id: str | None = None

    chief_complaints: str | None = None
    history_present_illness: str | None = None
    past_history: str | None = None
    family_history: str | None = None
    personal_history: str | None = None
    mental_generals: str | None = None
    physical_generals: str | None = None
    particulars: str | None = None
    female_history: str | None = None
    male_history: str | None = None
    sexual_reproductive_history: str | None = None
    obstetric_history: str | None = None
    surgical_history: str | None = None
    clinical_examination: str | None = None
    totality: str | None = None
    characteristic_symptoms: str | None = None
    miasmatic_assessment: str | None = None
    analytical_notes: str | None = None
    remedy_differential: str | None = None
    prescribing_rationale: str | None = None

    quick_generals: dict[str, Any] | None = None
    modalities: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_encounter(self) -> "CaseRecordCreate":
        if self.visit_id is not None and self.admission_id is not None:
            raise ValueError("A case record cannot belong to both visit and admission.")
        return self


class CaseRecordUpdate(BaseSchema):
    case_status: CaseStatus | None = None
    chief_complaints: str | None = None
    history_present_illness: str | None = None
    past_history: str | None = None
    family_history: str | None = None
    personal_history: str | None = None
    mental_generals: str | None = None
    physical_generals: str | None = None
    particulars: str | None = None
    female_history: str | None = None
    male_history: str | None = None
    sexual_reproductive_history: str | None = None
    obstetric_history: str | None = None
    surgical_history: str | None = None
    clinical_examination: str | None = None
    totality: str | None = None
    characteristic_symptoms: str | None = None
    miasmatic_assessment: str | None = None
    analytical_notes: str | None = None
    remedy_differential: str | None = None
    prescribing_rationale: str | None = None
    quick_generals: dict[str, Any] | None = None
    modalities: dict[str, Any] | None = None


class CaseRecordRead(CaseRecordCreate):
    id: int
    case_year: int
    storage_tier: str
    is_current_year: bool
    renewed_from_case_id: int | None = None
    case_number: str
    created_by: int
    created_at: datetime
    updated_at: datetime


__all__ = [
    "CaseStatus",
    "CaseRecordCreate",
    "CaseRecordUpdate",
    "CaseRecordRead",
]
