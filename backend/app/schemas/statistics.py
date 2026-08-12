"""Schemas for hospital statistics and deduplicated activity reporting."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StatisticsFilters(BaseModel):
    """Inclusive reporting period and optional master filters."""

    model_config = ConfigDict(extra="forbid")

    start_date: date
    end_date: date
    department_id: UUID | None = None
    service_id: UUID | None = None


class StatisticsCount(BaseModel):
    """Named count used by the statistics response."""

    name: str
    count: int = Field(ge=0)


class DepartmentStatistics(BaseModel):
    """Department-level activity summary."""

    department_id: UUID
    department_name: str
    activity_count: int = Field(ge=0)
    unique_patient_count: int = Field(ge=0)
    opd_count: int = Field(ge=0)
    ipd_count: int = Field(ge=0)
    investigation_count: int = Field(ge=0)
    service_count: int = Field(ge=0)
    male_count: int = Field(ge=0)
    female_count: int = Field(ge=0)
    other_gender_count: int = Field(ge=0)
    child_count: int = Field(ge=0)
    adult_count: int = Field(ge=0)
    unspecified_age_count: int = Field(ge=0)
    new_case_count: int = Field(ge=0)
    old_case_count: int = Field(ge=0)
    unspecified_case_count: int = Field(ge=0)
    inhouse_count: int = Field(ge=0)
    outsourced_count: int = Field(ge=0)


class ServiceStatistics(BaseModel):
    """Service/subsection activity summary."""

    service_id: UUID
    service_name: str
    department_id: UUID
    department_name: str
    activity_count: int = Field(ge=0)
    unique_patient_count: int = Field(ge=0)
    male_count: int = Field(ge=0)
    female_count: int = Field(ge=0)
    other_gender_count: int = Field(ge=0)
    child_count: int = Field(ge=0)
    adult_count: int = Field(ge=0)
    unspecified_age_count: int = Field(ge=0)
    new_case_count: int = Field(ge=0)
    old_case_count: int = Field(ge=0)
    unspecified_case_count: int = Field(ge=0)
    inhouse_count: int = Field(ge=0)
    outsourced_count: int = Field(ge=0)


class HospitalStatistics(BaseModel):
    """Deduplicated hospital statistics for a reporting period."""

    start_date: date
    end_date: date
    unique_hospital_patient_count: int = Field(ge=0)
    total_activity_count: int = Field(ge=0)
    opd_count: int = Field(ge=0)
    ipd_count: int = Field(ge=0)
    investigation_count: int = Field(ge=0)
    generic_service_count: int = Field(ge=0)
    male_patient_count: int = Field(ge=0)
    female_patient_count: int = Field(ge=0)
    other_gender_patient_count: int = Field(ge=0)
    child_patient_count: int = Field(ge=0)
    adult_patient_count: int = Field(ge=0)
    unspecified_age_patient_count: int = Field(ge=0)
    new_case_activity_count: int = Field(ge=0)
    old_case_activity_count: int = Field(ge=0)
    unspecified_case_activity_count: int = Field(ge=0)
    inhouse_investigation_count: int = Field(ge=0)
    outsourced_investigation_count: int = Field(ge=0)
    departments: list[DepartmentStatistics]
    services: list[ServiceStatistics]


__all__ = [
    "StatisticsFilters",
    "StatisticsCount",
    "DepartmentStatistics",
    "ServiceStatistics",
    "HospitalStatistics",
]
