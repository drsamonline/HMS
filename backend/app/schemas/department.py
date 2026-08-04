"""
Department schemas for HHMS.

Defines request and response DTOs for hospital departments.
"""

from __future__ import annotations

from uuid import UUID

from app.core.enums import DepartmentType
from app.schemas.base import BaseSchema


class DepartmentCreate(BaseSchema):
    """
    Schema used to create a department.
    """

    code: str

    name: str

    description: str | None = None

    department_type: DepartmentType


class DepartmentUpdate(BaseSchema):
    """
    Schema used to update a department.
    """

    code: str | None = None

    name: str | None = None

    description: str | None = None

    department_type: DepartmentType | None = None


class DepartmentRead(BaseSchema):
    """
    Schema returned by the API.
    """

    id: UUID

    code: str

    name: str

    description: str | None

    department_type: DepartmentType


__all__ = [
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentRead",
]