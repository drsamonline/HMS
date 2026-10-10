"""Regression tests for backend foundation corrections."""
from app.models.opd_token import OPDToken
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def test_opd_token_model_is_not_visit_model() -> None:
    assert OPDToken.__tablename__ == "OPDToken"
    assert OPDToken.__name__ == "OPDToken"


def test_department_master_supports_activation() -> None:
    created = DepartmentCreate(
        code="LAB",
        name="Laboratory",
        department_type="diagnostic",
    )
    updated = DepartmentUpdate(is_active=False)
    assert created.code == "LAB"
    assert updated.is_active is False
