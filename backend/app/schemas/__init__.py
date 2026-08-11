"""
Central public exports for Pydantic schemas used by the
Hospital Homoeopathic Management System.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.base import BaseSchema
from app.schemas.common import ErrorResponse, ResponseSchema
from app.schemas.health import HealthResponse
from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleRead,
    RoleUpdate,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserRead,
    UserUpdate,
)

__all__ = [
    # Base schema
    "BaseSchema",

    # Authentication
    "LoginRequest",
    "TokenResponse",

    # Common responses
    "ResponseSchema",
    "ErrorResponse",

    # Health
    "HealthResponse",

    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",

    # Role
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",
]