"""
HHMS Authentication Dependencies
================================

Provides reusable FastAPI authentication dependencies.

This module validates the authenticated request by extracting the
OAuth2 bearer token and validating its JWT payload.

User persistence, password authentication, authorization, role
validation, and permission checks belong to their respective
application layers.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Annotated, TypeAlias

from fastapi import Depends
from jwt import InvalidTokenError

from app.auth.jwt import decode_access_token
from app.auth.security import TokenDependency
from app.core.exceptions import AuthenticationException


CurrentUser: TypeAlias = dict[str, object]


def get_current_user(
    token: TokenDependency,
) -> CurrentUser:
    """
    Validate the current request's bearer token.

    Parameters
    ----------
    token : str
        OAuth2 bearer token extracted from the Authorization header.

    Returns
    -------
    CurrentUser
        Validated JWT payload.

    Raises
    ------
    AuthenticationException
        If the JWT is invalid, expired, malformed, incorrectly
        signed, or otherwise fails JWT validation.
    """

    try:
        payload = decode_access_token(token)

    except InvalidTokenError as exc:
        raise AuthenticationException(
            "Invalid or expired authentication token."
        ) from exc

    return payload


CurrentUserDependency = Annotated[
    CurrentUser,
    Depends(get_current_user),
]


__all__ = [
    "CurrentUser",
    "CurrentUserDependency",
    "get_current_user",
]