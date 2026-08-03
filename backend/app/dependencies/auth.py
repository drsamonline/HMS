"""
HHMS Authentication Dependencies

Provides authentication dependency interfaces used by FastAPI.

JWT validation, user retrieval, role validation, and permission
checks are implemented in the Authentication package.

This module intentionally contains only dependency declarations.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends

from app.core.exceptions import AuthenticationException


def get_current_user() -> Any:
    """
    Return the currently authenticated user.

    This dependency will be fully implemented in the
    Authentication package.

    Raises
    ------
    AuthenticationException
        Always until authentication is configured.
    """

    raise AuthenticationException(
        "Authentication has not been been configured."
    )


CurrentUserDependency = Annotated[
    Any,
    Depends(get_current_user),
]

__all__ = [
    "CurrentUserDependency",
    "get_current_user",
]