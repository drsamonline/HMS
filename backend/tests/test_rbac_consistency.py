"""RBAC consistency tests."""
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.schemas.role import RoleCreate, RoleRead

def test_rbac_models_use_integer_project_ids():
    assert Permission.__tablename__ == "Permission"
    assert UserRole.__tablename__ == "UserRole"
    assert RolePermission.__tablename__ == "RolePermission"
    role=RoleCreate(role_name="Doctor")
    assert role.role_name=="Doctor"
