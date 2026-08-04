"""
JWT utility functions for HHMS.

This module provides secure creation and validation of JSON Web Tokens.
It contains no authentication or user lookup logic.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.config.settings import Settings


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:
            Unique subject identifier.
        expires_delta:
            Optional custom expiry duration.
        additional_claims:
            Additional JWT claims.

    Returns:
        Encoded JWT string.
    """

    settings = Settings.get_settings()

    expire = datetime.now(UTC) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": datetime.now(UTC),
        "exp": expire,
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
    Decode and validate a JWT.

    Args:
        token:
            Encoded JWT.

    Returns:
        Decoded JWT payload.

    Raises:
        InvalidTokenError:
            If the token is invalid or expired.
    """

    settings = Settings.get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except InvalidTokenError:
        raise

    if "sub" not in payload:
        raise InvalidTokenError("JWT subject claim is missing.")

    return payload


__all__ = [
    "create_access_token",
    "decode_access_token",
]