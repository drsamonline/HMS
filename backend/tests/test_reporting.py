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


def test_reporting_sections_include_billing_documents_and_mrd() -> None:
    from app.schemas.reporting import ALL_REPORT_SECTIONS, ClinicalReportRequest

    assert "billing" in ALL_REPORT_SECTIONS
    assert "payments" in ALL_REPORT_SECTIONS
    assert "medical_documents" in ALL_REPORT_SECTIONS
    assert "mrd" in ALL_REPORT_SECTIONS
    request = ClinicalReportRequest(
        patient_id=1,
        sections=["billing", "payments", "medical_documents", "mrd"],
    )
    assert request.sections == ["billing", "payments", "medical_documents", "mrd"]


def test_print_envelope_schema_supports_custom_title() -> None:
    from app.schemas.reporting import ReportPrintEnvelopeRequest
    request = ReportPrintEnvelopeRequest(patient_id=1, title="Complete Case Report")
    assert request.title == "Complete Case Report"
