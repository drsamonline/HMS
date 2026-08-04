"""
Base Pydantic schema definitions for HHMS.

All application schemas should inherit from BaseSchema.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema for all HHMS DTOs.

    Provides common Pydantic configuration across the
    entire application.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )