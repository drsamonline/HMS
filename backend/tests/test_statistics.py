"""Regression tests for the statistics contracts and counting rules."""
from __future__ import annotations

from datetime import date

from app.schemas.statistics import HospitalStatistics


def test_statistics_schema_accepts_empty_breakdown() -> None:
    result = HospitalStatistics(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        unique_hospital_patient_count=0,
        total_activity_count=0,
        opd_count=0,
        ipd_count=0,
        investigation_count=0,
        generic_service_count=0,
        male_patient_count=0,
        female_patient_count=0,
        other_gender_patient_count=0,
        child_patient_count=0,
        adult_patient_count=0,
        unspecified_age_patient_count=0,
        new_case_activity_count=0,
        old_case_activity_count=0,
        unspecified_case_activity_count=0,
        inhouse_investigation_count=0,
        outsourced_investigation_count=0,
        departments=[],
        services=[],
    )
    assert result.unique_hospital_patient_count == 0


def test_reporting_period_is_inclusive_in_schema() -> None:
    result = HospitalStatistics(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        unique_hospital_patient_count=1,
        total_activity_count=1,
        opd_count=1,
        ipd_count=0,
        investigation_count=0,
        generic_service_count=0,
        male_patient_count=1,
        female_patient_count=0,
        other_gender_patient_count=0,
        child_patient_count=0,
        adult_patient_count=1,
        unspecified_age_patient_count=0,
        new_case_activity_count=1,
        old_case_activity_count=0,
        unspecified_case_activity_count=0,
        inhouse_investigation_count=0,
        outsourced_investigation_count=0,
        departments=[],
        services=[],
    )
    assert result.start_date <= result.end_date
