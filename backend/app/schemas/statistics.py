"""Schemas for deduplicated hospital statistics reporting."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StatisticsFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: date
    end_date: date
    department_id: UUID | None = None
    service_id: UUID | None = None


class ActivityBreakdown(BaseModel):
    """Named activity count for report-level breakdowns."""
    name: str
    count: int = Field(ge=0)


class ServiceTypeStatistics(BaseModel):
    """Activity grouped by configurable service type/category."""
    service_type: str
    activity_count: int = Field(ge=0)
    unique_patient_count: int = Field(ge=0)


class DepartmentStatistics(BaseModel):
    department_id: UUID
    department_name: str
    department_type: str = Field(default="", description="Configurable department classification.")
    activity_count: int = Field(ge=0)
    unique_patient_count: int = Field(ge=0)
    opd_count: int = Field(ge=0)
    ipd_count: int = Field(ge=0)
    investigation_count: int = Field(ge=0)
    service_count: int = Field(ge=0)
    male_count: int = Field(ge=0, description="Distinct male patients with activity in this department.")
    female_count: int = Field(ge=0, description="Distinct female patients with activity in this department.")
    other_gender_count: int = Field(ge=0)
    child_count: int = Field(ge=0, description="Distinct patients under 18.")
    adult_count: int = Field(ge=0, description="Distinct patients 18 or older.")
    unspecified_age_count: int = Field(ge=0)
    new_case_count: int = Field(ge=0, description="Activity rows classified as new.")
    old_case_count: int = Field(ge=0, description="Activity rows classified as old.")
    unspecified_case_count: int = Field(ge=0)
    inhouse_count: int = Field(ge=0)
    outsourced_count: int = Field(ge=0)


class ServiceStatistics(BaseModel):
    service_id: UUID
    service_name: str
    department_id: UUID
    department_name: str
    department_type: str = Field(default="", description="Configurable department classification.")
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
    service_type: str = Field(default="", description="Configurable service/subsection classification.")
    opd_count: int = Field(ge=0)
    ipd_count: int = Field(ge=0)
    investigation_count: int = Field(ge=0)
    generic_service_count: int = Field(ge=0)


class DailyStatistics(BaseModel):
    date: date
    unique_patient_count: int = Field(ge=0)
    activity_count: int = Field(ge=0)
    opd_count: int = Field(ge=0)
    ipd_count: int = Field(ge=0)
    investigation_count: int = Field(ge=0)
    service_count: int = Field(ge=0)


class HospitalStatistics(BaseModel):
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
    activity_type_breakdown: list[ActivityBreakdown]
    case_type_breakdown: list[ActivityBreakdown]
    fulfillment_breakdown: list[ActivityBreakdown]
    service_type_breakdown: list[ServiceTypeStatistics]
    departments: list[DepartmentStatistics]
    services: list[ServiceStatistics]
    daily: list[DailyStatistics]


__all__ = [
    "StatisticsFilters",
    "ActivityBreakdown",
    "ServiceTypeStatistics",
    "DepartmentStatistics",
    "ServiceStatistics",
    "DailyStatistics",
    "HospitalStatistics",
]
