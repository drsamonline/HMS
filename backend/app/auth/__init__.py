"""
Authentication foundation package for HHMS.

This package provides reusable security utilities used by the
authentication subsystem.

Modules
-------
jwt
    JWT creation and validation utilities.

password
    Password hashing and verification helpers.

security
    FastAPI security dependencies.
"""

from __future__ import annotations

from app.auth.jwt import (
    create_access_token,
    decode_access_token,
)
from app.auth.password import (
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.auth.security import (
    TokenDependency,
    get_bearer_token,
    oauth2_scheme,
)

__all__ = [
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
    "password_needs_rehash",
    "oauth2_scheme",
    "TokenDependency",
    "get_bearer_token",
]