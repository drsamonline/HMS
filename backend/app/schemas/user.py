"""
HHMS User Schemas
=================

Pydantic request and response schemas for the User entity.

These schemas define the API boundary for user data and must not
be confused with the SQLAlchemy ORM model in ``app.models.user``.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


_EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


class UserBase(BaseSchema):
    """
    Common user fields shared by create, update, and read schemas.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique login username.",
        examples=["admin"],
    )

    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="User email address.",
        examples=["admin@example.com"],
    )

    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's full name.",
        examples=["System Administrator"],
    )

    @field_validator(
        "username",
        "full_name",
        mode="before",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        """
        Normalize and validate required textual fields.
        """

        if not isinstance(value, str):
            raise ValueError(
                "Value must be a string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Value must not be empty."
            )

        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(
        cls,
        value: str,
    ) -> str:
        """
        Perform basic structural email validation.

        Full mailbox verification is outside the responsibility
        of the schema layer.
        """

        normalized = value.strip().lower()

        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Invalid email address format."
            )

        return normalized


class UserCreate(UserBase):
    """
    Schema used to create a new user.

    The plaintext password is accepted only at the API boundary.
    It must be hashed before persistence.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password supplied during account creation.",
    )

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value: str,
    ) -> str:
        """
        Validate basic password requirements.

        Password hashing is performed outside the schema layer.
        """

        if not value.strip():
            raise ValueError(
                "Password must not be empty."
            )

        return value


class UserUpdate(BaseSchema):
    """
    Schema used to update an existing user.

    All fields are optional because updates may modify only a
    subset of the user's profile.
    """

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Unique login username.",
    )

    email: str | None = Field(
        default=None,
        min_length=5,
        max_length=255,
        description="User email address.",
    )

    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="User's full name.",
    )

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="New plaintext password.",
    )

    is_active: bool | None = Field(
        default=None,
        description="Whether the user account is active.",
    )

    @field_validator(
        "username",
        "full_name",
        mode="before",
    )
    @classmethod
    def validate_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize optional textual fields.
        """

        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "Value must be a string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Value must not be empty."
            )

        return normalized

    @field_validator("email")
    @classmethod
    def validate_optional_email(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize and validate an optional email address.
        """

        if value is None:
            return None

        normalized = value.strip().lower()

        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Invalid email address format."
            )

        return normalized

    @field_validator("password")
    @classmethod
    def validate_optional_password(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Validate an optional replacement password.
        """

        if value is None:
            return None

        if not value.strip():
            raise ValueError(
                "Password must not be empty."
            )

        return value


class UserRead(UserBase):
    """
    Schema returned by the API for an authenticated user record.

    Sensitive authentication material is deliberately excluded.
    """

    id: UUID

    is_superuser: bool

    is_active: bool

    created_at: datetime

    updated_at: datetime


__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
]