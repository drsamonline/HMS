"""
HHMS CRUD package.

Provides reusable CRUD infrastructure and entity-specific CRUD
operations for the Hospital Homoeopathic Management System.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.crud.base import CRUDBase
from app.crud.department import DepartmentCRUD, department_crud
from app.crud.designation import DesignationCRUD, designation_crud
from app.crud.permission import PermissionCRUD, permission_crud
from app.crud.role import RoleCRUD, role_crud
from app.crud.role_permission import (
    RolePermissionCRUD,
    role_permission_crud,
)
from app.crud.user import UserCRUD, user_crud
from app.crud.user_role import UserRoleCRUD, user_role_crud

__all__ = [
    "CRUDBase",
    "DepartmentCRUD",
    "department_crud",
    "DesignationCRUD",
    "designation_crud",
    "PermissionCRUD",
    "permission_crud",
    "RoleCRUD",
    "role_crud",
    "RolePermissionCRUD",
    "role_permission_crud",
    "UserCRUD",
    "user_crud",
    "UserRoleCRUD",
    "user_role_crud",
]