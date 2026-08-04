"""
HHMS schema package.

Exports all public schema classes used throughout the
application.
"""

from __future__ import annotations

from app.schemas.base import BaseSchema
from app.schemas.common import ErrorResponse, ResponseSchema
from app.schemas.health import HealthResponse

__all__ = [
    "BaseSchema",
    "ResponseSchema",
    "ErrorResponse",
    "HealthResponse",
]