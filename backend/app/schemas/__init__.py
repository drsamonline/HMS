"""
Central public exports for Pydantic schemas used by the
Hospital Homoeopathic Management System.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.base import BaseSchema
from app.schemas.common import ErrorResponse, ResponseSchema
from app.schemas.department import (
    DepartmentBase,
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
)
from app.schemas.designation import (
    DesignationBase,
    DesignationCreate,
    DesignationRead,
    DesignationUpdate,
)
from app.schemas.health import HealthResponse
from app.schemas.permission import (
    PermissionBase,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
)
from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleRead,
    RoleUpdate,
)
from app.schemas.role_permission import (
    RolePermissionCreate,
    RolePermissionRead,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.schemas.user_role import (
    UserRoleCreate,
    UserRoleRead,
)

__all__ = [
    # Base schema
    "BaseSchema",

    # Authentication
    "LoginRequest",
    "TokenResponse",

    # Common responses
    "ResponseSchema",
    "ErrorResponse",

    # Health
    "HealthResponse",

    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",

    # Role
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",

    # Permission
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionRead",

    # User-Role
    "UserRoleCreate",
    "UserRoleRead",

    # Role-Permission
    "RolePermissionCreate",
    "RolePermissionRead",

    # Hospital master data
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentRead",
    "DesignationBase",
    "DesignationCreate",
    "DesignationUpdate",
    "DesignationRead",
]