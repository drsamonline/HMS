"""Reporting selection contract tests."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.reporting import ALL_REPORT_SECTIONS, ClinicalReportRequest


def test_report_requires_a_scope() -> None:
    with pytest.raises(ValidationError):
        ClinicalReportRequest()


def test_report_rejects_reverse_date_range() -> None:
    with pytest.raises(ValidationError):
        ClinicalReportRequest(
            patient_id=1,
            start_datetime=datetime(2026, 8, 13, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 8, 12, tzinfo=timezone.utc),
        )


def test_empty_sections_means_complete_supported_report_scope() -> None:
    request = ClinicalReportRequest(patient_id=1)
    assert request.sections == []
    assert len(ALL_REPORT_SECTIONS) >= 10


def test_selected_sections_are_preserved() -> None:
    request = ClinicalReportRequest(
        patient_id=1,
        sections=["case_record", "diagnosis", "prescriptions"],
    )
    assert request.sections == ["case_record", "diagnosis", "prescriptions"]
