"""Regression tests for statistics reporting contracts and deduplication semantics."""
from __future__ import annotations

from datetime import date

import pytest

from app.schemas.statistics import DailyStatistics, HospitalStatistics
from app.services.statistics import _period_bounds


def test_period_bounds_are_inclusive_of_end_date() -> None:
    start, end = _period_bounds(date(2026, 8, 1), date(2026, 8, 31))
    assert start.isoformat() == "2026-08-01T00:00:00"
    assert end.isoformat() == "2026-09-01T00:00:00"


def test_invalid_reporting_period_is_rejected() -> None:
    with pytest.raises(ValueError):
        _period_bounds(date(2026, 9, 1), date(2026, 8, 31))


def test_daily_statistics_contract() -> None:
    row = DailyStatistics(
        date=date(2026, 8, 12),
        unique_patient_count=10,
        activity_count=15,
        opd_count=10,
        ipd_count=2,
        investigation_count=2,
        service_count=1,
    )
    assert row.unique_patient_count == 10
    assert row.activity_count == 15


def test_hospital_statistics_allows_empty_period() -> None:
    result = HospitalStatistics(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 1),
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
        daily=[],
    )
    assert result.unique_hospital_patient_count == 0


def test_statistics_schema_keeps_unique_patient_and_activity_counts_separate() -> None:
    result = HospitalStatistics(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 1),
        unique_hospital_patient_count=1,
        total_activity_count=3,
        opd_count=1,
        ipd_count=0,
        investigation_count=2,
        generic_service_count=0,
        male_patient_count=1,
        female_patient_count=0,
        other_gender_patient_count=0,
        child_patient_count=0,
        adult_patient_count=1,
        unspecified_age_patient_count=0,
        new_case_activity_count=3,
        old_case_activity_count=0,
        unspecified_case_activity_count=0,
        inhouse_investigation_count=1,
        outsourced_investigation_count=1,
        departments=[],
        services=[],
        daily=[],
    )
    assert result.unique_hospital_patient_count == 1
    assert result.total_activity_count == 3


def test_department_and_service_breakdown_contracts() -> None:
    from app.schemas.statistics import DepartmentStatistics, ServiceStatistics
    from uuid import uuid4

    department = DepartmentStatistics(
        department_id=uuid4(),
        department_name="Laboratory",
        department_type="diagnostic",
        activity_count=10,
        unique_patient_count=8,
        opd_count=2,
        ipd_count=1,
        investigation_count=7,
        service_count=0,
        male_count=4,
        female_count=4,
        other_gender_count=0,
        child_count=1,
        adult_count=7,
        unspecified_age_count=0,
        new_case_count=6,
        old_case_count=4,
        unspecified_case_count=0,
        inhouse_count=5,
        outsourced_count=2,
    )
    service = ServiceStatistics(
        service_id=uuid4(),
        service_name="Hematology",
        service_type="hematology",
        department_id=department.department_id,
        department_name="Laboratory",
        activity_count=7,
        unique_patient_count=6,
        male_count=3,
        female_count=3,
        other_gender_count=0,
        child_count=1,
        adult_count=5,
        unspecified_age_count=0,
        new_case_count=4,
        old_case_count=3,
        unspecified_case_count=0,
        inhouse_count=4,
        outsourced_count=3,
        opd_count=0,
        ipd_count=0,
        investigation_count=7,
        generic_service_count=0,
    )
    assert department.department_type == "diagnostic"
    assert service.service_type == "hematology"
    assert service.investigation_count == 7


def test_breakdown_contracts() -> None:
    from app.schemas.statistics import ActivityBreakdown, ServiceTypeStatistics

    activity = ActivityBreakdown(name="investigation", count=7)
    fulfillment = ActivityBreakdown(name="inhouse", count=5)
    service_type = ServiceTypeStatistics(
        service_type="hematology",
        activity_count=7,
        unique_patient_count=6,
    )

    assert activity.count == 7
    assert fulfillment.name == "inhouse"
    assert service_type.service_type == "hematology"


def test_department_stats_does_not_select_service_type_without_grouping() -> None:
    from pathlib import Path
    source = Path("backend/app/services/statistics.py").read_text(encoding="utf-8")
    department_section = source.split("async def _department_stats", 1)[1].split("async def _service_stats", 1)[0]
    assert "DepartmentService.service_type.label" not in department_section
