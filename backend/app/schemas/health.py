"""
Health response schemas for HHMS API.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


class HealthResponse(BaseSchema):
    """
    Health endpoint response schema.

    Used by the liveness, readiness and health endpoints.
    """

    status: Literal["healthy"] = Field(
        default="healthy",
        description="Current health status of the service.",
    )

    service: str = Field(
        ...,
        description="Application service name.",
        examples=["HHMS"],
    )

    version: str = Field(
        ...,
        description="Application version.",
        examples=["1.0.0"],
    )


__all__ = [
    "HealthResponse",
]