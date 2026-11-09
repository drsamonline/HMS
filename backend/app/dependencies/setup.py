"""The setup authorisation dependency.

A setup token is a JWT with ``scope: setup``. It is not a login: ``get_current_user``
does not accept it, and this dependency does not accept a login. The two cannot be
substituted for each other.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def require_setup_token(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A setup token is required. Unlock the wizard with the setup code.",
        )
    try:
        payload = decode_access_token(token)
    except Exception as exc:  # noqa: BLE001 - any decode failure is the same answer
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The setup token is invalid or has expired.",
        ) from exc

    if payload.get("scope") != "setup":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This token is not a setup token.",
        )
    return payload


SetupAuthorised = Annotated[dict, Depends(require_setup_token)]

__all__ = ["SetupAuthorised", "require_setup_token"]
