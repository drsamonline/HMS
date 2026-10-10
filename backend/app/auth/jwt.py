"""
Provides secure creation and validation of JSON Web Tokens.

This module is deliberately limited to JWT operations. User lookup,
authentication workflows, authorization, and database access belong
to their respective application layers.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.config.settings import get_settings


_RESERVED_CLAIMS = frozenset(
    {
        "sub",
        "iat",
        "exp",
    }
)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Parameters
    ----------
    subject : str
        Unique identifier for the token subject.

    expires_delta : timedelta | None
        Optional custom token lifetime. When omitted, the
        configured ACCESS_TOKEN_EXPIRE_MINUTES value is used.

    additional_claims : dict[str, Any] | None
        Optional additional non-reserved JWT claims.

    Returns
    -------
    str
        Encoded and signed JWT.

    Raises
    ------
    ValueError
        If the subject is empty or additional claims attempt to
        override reserved JWT claims.
    """

    normalized_subject = subject.strip()

    if not normalized_subject:
        raise ValueError(
            "JWT subject must not be empty."
        )

    if expires_delta is not None and expires_delta <= timedelta(0):
        raise ValueError(
            "JWT expiration duration must be positive."
        )

    if additional_claims:
        reserved_claims = _RESERVED_CLAIMS.intersection(
            additional_claims
        )

        if reserved_claims:
            reserved = ", ".join(
                sorted(reserved_claims)
            )

            raise ValueError(
                f"Additional claims cannot override reserved "
                f"JWT claims: {reserved}."
            )

    settings = get_settings()

    issued_at = datetime.now(UTC)

    lifetime = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    expires_at = issued_at + lifetime

    payload: dict[str, Any] = {
        "sub": normalized_subject,
        "iat": issued_at,
        "exp": expires_at,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Parameters
    ----------
    token : str
        Encoded JWT access token.

    Returns
    -------
    dict[str, Any]
        Validated JWT payload.

    Raises
    ------
    InvalidTokenError
        If the token is malformed, expired, incorrectly signed,
        uses an invalid algorithm, or lacks a subject claim.
    """

    if not token or not token.strip():
        raise InvalidTokenError(
            "JWT token must not be empty."
        )

    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={
            "require": [
                "sub",
                "iat",
                "exp",
            ],
        },
    )

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.strip():
        raise InvalidTokenError(
            "JWT subject claim is missing or invalid."
        )

    return payload


__all__ = [
    "create_access_token",
    "decode_access_token",
]