"""
Permission schemas for HHMS.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class PermissionBase(BaseSchema):
    """
    Base schema shared by permission DTOs.
    """

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Human-readable permission name.",
    )

    code: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Unique permission code.",
        examples=["patient:create"],
    )

    module: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Functional module name.",
        examples=["Patient"],
    )

    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional permission description.",
    )


class PermissionCreate(PermissionBase):
    """
    Schema used to create a permission.
    """


class PermissionUpdate(BaseSchema):
    """
    Schema used to update a permission.
    """

    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class PermissionRead(PermissionBase):
    """
    Schema returned by the API.
    """

    id: UUID

    is_active: bool


__all__ = [
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionRead",
]