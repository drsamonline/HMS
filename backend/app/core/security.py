"""
HHMS Security Utilities

Provides password hashing and verification utilities.

Authentication, JWT handling, and authorization will be
implemented in the Authentication package.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from passlib.context import CryptContext

from app.core.exceptions import AuthenticationException


_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password.

    Parameters
    ----------
    password : str
        Plain-text password.

    Returns
    -------
    str
        Secure password hash.
    """
    return _pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a password against its hash.

    Parameters
    ----------
    plain_password : str
        User supplied password.

    hashed_password : str
        Stored password hash.

    Returns
    -------
    bool
        True if password is valid.

    Raises
    ------
    AuthenticationException
        If password verification fails because of an
        invalid hash.
    """

    try:
        return _pwd_context.verify(
            plain_password,
            hashed_password,
        )

    except (ValueError, TypeError) as exc:
        raise AuthenticationException(
            "Invalid password hash."
        ) from exc


def needs_rehash(hashed_password: str) -> bool:
    """
    Determine whether an existing password hash should
    be regenerated using the current hashing policy.

    Parameters
    ----------
    hashed_password : str

    Returns
    -------
    bool
    """

    return _pwd_context.needs_update(hashed_password)