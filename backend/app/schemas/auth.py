"""
Authentication-related Pydantic schemas for HHMS.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """
    Credentials submitted during authentication.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    username: str = Field(
        min_length=1,
        max_length=150,
    )

    password: str = Field(
        min_length=1,
        max_length=256,
    )


class TokenResponse(BaseModel):
    """
    JWT authentication response.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    access_token: str
    token_type: str = "bearer"


__all__ = [
    "LoginRequest",
    "TokenResponse",
]