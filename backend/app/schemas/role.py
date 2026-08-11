"""
HHMS Role Schemas
=================

Pydantic request and response schemas for the Role entity.

The SQLAlchemy ORM model is defined separately in
``app.models.role``.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class RoleBase(BaseSchema):
    """
    Common role fields shared by create and read schemas.
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Human-readable role name.",
        examples=["Administrator"],
    )

    code: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Unique role code.",
        examples=["administrator"],
    )

    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional role description.",
    )

    @field_validator("name", "code")
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        """
        Normalize required role text fields.
        """

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Value must not be empty."
            )

        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize an optional role description.
        """

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


class RoleCreate(RoleBase):
    """
    Schema used to create a role.
    """


class RoleUpdate(BaseSchema):
    """
    Schema used to update a role.

    The role code is intentionally immutable because it is the
    stable identifier used by RBAC logic and permission mappings.
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Human-readable role name.",
    )

    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional role description.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize an optional role name.
        """

        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Role name must not be empty."
            )

        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize an optional role description.
        """

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


class RoleRead(RoleBase):
    """
    Schema returned by the API for a role.
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