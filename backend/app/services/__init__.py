"""
Public exports for the HHMS application Service Layer.

Services coordinate business workflows and transaction boundaries.
Database access remains encapsulated by repositories.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.services.auth import (
    AuthService,
    auth_service,
)
from app.services.user import (
    UserService,
    user_service,
)

__all__ = [
    "AuthService",
    "auth_service",
    "UserService",
    "user_service",
]