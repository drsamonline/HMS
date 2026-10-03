"""
Designation schemas for HHMS.

Defines request and response DTOs for staff designations.
"""

from __future__ import annotations

from uuid import UUID

from app.core.enums import DesignationType
from app.schemas.base import BaseSchema


class DesignationBase(BaseSchema):
    """
    Shared attributes for designation request and response DTOs.
    """

    code: str

    name: str

    description: str | None = None

    designation_type: DesignationType


class DesignationCreate(DesignationBase):
    """
    Schema used to create a designation.
    """


class DesignationUpdate(BaseSchema):
    """
    Schema used to update a designation.
    """

    code: str | None = None

    name: str | None = None

    description: str | None = None

    designation_type: DesignationType | None = None


class DesignationRead(DesignationBase):
    """
    Schema returned by the API.
    """

    id: UUID


__all__ = [
    "DesignationBase",
    "DesignationCreate",
    "DesignationUpdate",
    "DesignationRead",
]