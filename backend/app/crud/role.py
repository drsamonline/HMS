"""
Role schemas for HHMS.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class RoleBase(BaseSchema):
    """
    Base schema shared by role DTOs.
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Human-readable role name.",
    )

    code: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Unique immutable role code.",
        examples=["administrator"],
    )

    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional role description.",
    )


class RoleCreate(RoleBase):
    """
    Schema used to create a role.
    """


class RoleUpdate(BaseSchema):
    """
    Schema used to update a role.
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class RoleRead(RoleBase):
    """
    Schema returned by the API.
    """

    id: UUID

    is_active: bool

    is_system: bool


__all__ = [
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",
]