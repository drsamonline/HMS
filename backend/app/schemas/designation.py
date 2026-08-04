"""
Designation schemas for HHMS.

Defines request and response DTOs for staff designations.
"""

from __future__ import annotations

from uuid import UUID

from app.core.enums import DesignationType
from app.schemas.base import BaseSchema


class DesignationCreate(BaseSchema):
    """
    Schema used to create a designation.
    """

    code: str

    name: str

    description: str | None = None

    designation_type: DesignationType


class DesignationUpdate(BaseSchema):
    """
    Schema used to update a designation.
    """

    code: str | None = None

    name: str | None = None

    description: str | None = None

    designation_type: DesignationType | None = None


class DesignationRead(BaseSchema):
    """
    Schema returned by the API.
    """

    id: UUID

    code: str

    name: str

    description: str | None

    designation_type: DesignationType


__all__ = [
    "DesignationCreate",
    "DesignationUpdate",
    "DesignationRead",
]