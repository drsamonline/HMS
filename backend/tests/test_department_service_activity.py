"""Import and schema tests for department services and activities."""
from uuid import uuid4

from app.schemas.department_service import DepartmentServiceCreate
from app.schemas.service_activity import ServiceActivityCreate


def test_department_service_schema_supports_hierarchy() -> None:
    department_id = uuid4()
    parent_id = uuid4()
    data = DepartmentServiceCreate(
        department_id=department_id,
        parent_service_id=parent_id,
        code="HEMA",
        name="Hematology",
        supports_fulfillment_mode=True,
    )
    assert data.department_id == department_id
    assert data.parent_service_id == parent_id


def test_service_activity_defaults_to_new_completed() -> None:
    data = ServiceActivityCreate(
        patient_id=1,
        department_id=uuid4(),
        service_id=uuid4(),
        activity_datetime="2026-08-12T10:00:00Z",
    )
    assert data.case_type == "new"
    assert data.status == "completed"
