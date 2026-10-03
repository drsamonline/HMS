"""Regression tests for clinical department/service classification."""
from uuid import uuid4

from app.schemas.admission import AdmissionCreate
from app.schemas.investigation import InvestigationCreate
from app.schemas.visit import VisitCreate


def test_visit_classification_is_optional() -> None:
    data = VisitCreate(
        patient_id=1,
        visit_type="OPD",
        visit_datetime="2026-08-12T10:00:00Z",
        consulting_doctor_id=1,
    )
    assert data.department_id is None
    assert data.service_id is None
    assert data.case_type is None


def test_admission_classification_is_optional() -> None:
    data = AdmissionCreate(
        patient_id=1,
        admission_datetime="2026-08-12T10:00:00Z",
        bed_id=1,
        admitted_by=1,
    )
    assert data.department_id is None
    assert data.service_id is None
    assert data.case_type is None


def test_investigation_supports_department_service_and_fulfillment() -> None:
    department_id = uuid4()
    service_id = uuid4()
    data = InvestigationCreate(
        patient_id=1,
        visit_id=2,
        department_id=department_id,
        service_id=service_id,
        case_type="old",
        fulfillment_mode="outsourced",
        investigation_name="CBC",
        requested_by=1,
        requested_datetime="2026-08-12T10:00:00Z",
    )
    assert data.department_id == department_id
    assert data.service_id == service_id
    assert data.case_type == "old"
    assert data.fulfillment_mode == "outsourced"
