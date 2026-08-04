"""
Security dependencies for HHMS.

This module provides reusable FastAPI security dependencies.
It intentionally contains no authentication or authorization logic.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True,
)


TokenDependency = Annotated[
    str,
    Depends(oauth2_scheme),
]


def get_bearer_token(
    token: TokenDependency,
) -> str:
    """
    Extract the bearer token from the current request.

    Args:
        token:
            OAuth2 bearer token.

    Returns:
        The raw JWT access token.
    """
    return token


__all__ = [
    "oauth2_scheme",
    "TokenDependency",
    "get_bearer_token",
]