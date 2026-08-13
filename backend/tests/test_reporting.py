"""Tests for Reporting/Print-Data Batch 02."""
from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.reporting import (
    ALL_REPORT_SECTIONS,
    ClinicalReportBatchRequest,
    ClinicalReportRequest,
)


def test_admission_is_a_supported_report_section() -> None:
    assert "admission" in ALL_REPORT_SECTIONS
    request = ClinicalReportRequest(patient_id=1, sections=["patient", "admission"])
    assert request.sections == ["patient", "admission"]


def test_batch_report_request_supports_period_and_case_filter() -> None:
    request = ClinicalReportBatchRequest(
        start_datetime=datetime(2026, 8, 1, tzinfo=ZoneInfo("Asia/Kolkata")),
        end_datetime=datetime(2026, 8, 31, 23, 59, 59, tzinfo=ZoneInfo("Asia/Kolkata")),
        case_status="active",
        limit=25,
    )
    assert request.case_status == "active"
    assert request.limit == 25
