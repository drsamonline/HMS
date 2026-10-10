"""
HHMS Core Security Compatibility Layer
=======================================

Compatibility interface for password security utilities.

The authoritative password hashing implementation is maintained
in ``app.auth.password``. This module preserves the historical
``app.core.security`` import path without maintaining a second
password hashing implementation.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.auth.password import (
    hash_password,
    password_needs_rehash,
    verify_password,
)


def needs_rehash(
    hashed_password: str,
) -> bool:
    """
    Determine whether an existing password hash should be rehashed.

    This function preserves the legacy ``needs_rehash`` API while
    delegating the actual policy decision to the authoritative
    password security module.
    """

    return password_needs_rehash(
        hashed_password,
    )


__all__ = [
    "hash_password",
    "verify_password",
    "needs_rehash",
]