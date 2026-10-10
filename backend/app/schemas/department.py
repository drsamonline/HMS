"""
Department schemas for HHMS.

Defines request and response DTOs for hospital departments.
"""

from __future__ import annotations

from uuid import UUID

from app.core.enums import DepartmentType
from app.schemas.base import BaseSchema


class DepartmentBase(BaseSchema):
    """
    Shared attributes for department request and response DTOs.
    """

    code: str

    name: str

    description: str | None = None

    department_type: DepartmentType


class DepartmentCreate(DepartmentBase):
    """
    Schema used to create a department.
    """


class DepartmentUpdate(BaseSchema):
    """
    Schema used to update a department.
    """

    code: str | None = None

    name: str | None = None

    description: str | None = None

    department_type: DepartmentType | None = None

    is_active: bool | None = None


class DepartmentRead(DepartmentBase):
    """
    Schema returned by the API.
    """

    id: UUID

    is_active: bool


__all__ = [
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentRead",
]