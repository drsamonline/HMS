"""HHMS reporting and print-selection schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema

ReportSection = Literal[
    "patient",
    "case_record",
    "admission",
    "diagnosis",
    "followups",
    "prescriptions",
    "investigations",
    "ipd_assessment",
    "pain_assessments",
    "nutritional_assessment",
    "diet_charts",
    "progress_notes",
    "discharge",
    "billing",
    "payments",
    "medical_documents",
    "mrd",
]

ALL_REPORT_SECTIONS: tuple[str, ...] = (
    "patient",
    "case_record",
    "admission",
    "diagnosis",
    "followups",
    "prescriptions",
    "investigations",
    "ipd_assessment",
    "pain_assessments",
    "nutritional_assessment",
    "diet_charts",
    "progress_notes",
    "discharge",
    "billing",
    "payments",
    "medical_documents",
    "mrd",
)

class ClinicalReportRequest(BaseSchema):
    patient_id: int | None = Field(default=None, gt=0)
    case_record_id: int | None = Field(default=None, gt=0)
    admission_id: int | None = Field(default=None, gt=0)
    sections: list[ReportSection] = Field(default_factory=list, max_length=len(ALL_REPORT_SECTIONS))
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "ClinicalReportRequest":
        if self.patient_id is None and self.case_record_id is None and self.admission_id is None:
            raise ValueError("patient_id, case_record_id, or admission_id is required.")
        if self.start_datetime and self.end_datetime and self.start_datetime > self.end_datetime:
            raise ValueError("start_datetime must not be later than end_datetime.")
        return self

class ClinicalReportRead(BaseSchema):
    report_type: Literal["clinical"] = "clinical"
    patient_id: int
    case_record_id: int | None = None
    admission_id: int | None = None
    sections: list[str]
    data: dict

class ClinicalReportBatchRequest(BaseSchema):
    start_datetime: datetime
    end_datetime: datetime
    patient_id: int | None = Field(default=None, gt=0)
    case_status: Literal["draft", "active", "closed"] | None = None
    sections: list[ReportSection] = Field(default_factory=list, max_length=len(ALL_REPORT_SECTIONS))
    limit: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def validate_range(self) -> "ClinicalReportBatchRequest":
        if self.start_datetime > self.end_datetime:
            raise ValueError("start_datetime must not be later than end_datetime.")
        return self

class ClinicalReportBatchItem(BaseSchema):
    case_record_id: int
    patient_id: int
    case_number: str
    case_status: str
    report: ClinicalReportRead

class ClinicalReportBatchRead(BaseSchema):
    report_type: Literal["clinical_batch"] = "clinical_batch"
    start_datetime: datetime
    end_datetime: datetime
    count: int = Field(ge=0)
    truncated: bool = False
    reports: list[ClinicalReportBatchItem]

class ReportCatalogItem(BaseSchema):
    key: str
    label: str
    description: str
    available_for: list[str]

class ReportCatalogRead(BaseSchema):
    report_type: Literal["catalog"] = "catalog"
    sections: list[ReportCatalogItem]

__all__ = [
    "ReportSection",
    "ALL_REPORT_SECTIONS",
    "ClinicalReportRequest",
    "ClinicalReportRead",
    "ClinicalReportBatchRequest",
    "ClinicalReportBatchItem",
    "ClinicalReportBatchRead",
    "ReportCatalogItem",
    "ReportCatalogRead",
]
