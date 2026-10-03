"""
Password hashing utilities for HHMS.

This module provides secure password hashing and verification
using Argon2 through pwdlib.
"""

from __future__ import annotations

from pwdlib import PasswordHash

_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plaintext password.

    Args:
        password:
            Plaintext password.

    Returns:
        Secure password hash.
    """
    return _password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plaintext password against its hash.

    Args:
        plain_password:
            User supplied password.

        hashed_password:
            Stored password hash.

    Returns:
        True if the password matches.
    """
    return _password_hasher.verify(
        plain_password,
        hashed_password,
    )


def password_needs_rehash(
    hashed_password: str,
) -> bool:
    """
    Determine whether a stored password should be rehashed.

    Args:
        hashed_password:
            Existing password hash.

    Returns:
        True if rehashing is recommended.
    """
    return _password_hasher.needs_rehash(
        hashed_password,
    )


__all__ = [
    "hash_password",
    "verify_password",
    "password_needs_rehash",
]