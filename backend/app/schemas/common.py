"""
Common reusable response schemas for HHMS.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import Field

from app.schemas.base import BaseSchema

T = TypeVar("T")


class ResponseSchema(BaseSchema, Generic[T]):
    """
    Standard successful API response.

    Attributes:
        success: Indicates whether the request succeeded.
        message: Optional informational message.
        data: Response payload.
    """

    success: bool = Field(
        default=True,
        description="Indicates whether the request was successful.",
    )

    message: str | None = Field(
        default=None,
        description="Optional response message.",
    )

    data: T | None = Field(
        default=None,
        description="Response payload.",
    )


class ErrorResponse(BaseSchema):
    """
    Standard API error response.
    """

    success: bool = Field(
        default=False,
        description="Always False for error responses.",
    )

    error: str = Field(
        ...,
        description="Human-readable error message.",
    )

    error_code: str | None = Field(
        default=None,
        description="Application-specific error code.",
    )

    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error information.",
    )


__all__ = [
    "ResponseSchema",
    "ErrorResponse",
]