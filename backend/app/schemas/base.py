"""
HHMS Base Pydantic Schemas
==========================

Provides the common Pydantic schema configuration used by all
HHMS API data-transfer objects.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema for all HHMS Pydantic models.

    Provides consistent validation and ORM serialization behavior
    throughout the application.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


__all__ = [
    "BaseSchema",
]