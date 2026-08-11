"""
HHMS Authentication API
=======================

HTTP endpoints for user authentication.

The endpoint layer is responsible only for HTTP concerns:
request parsing, dependency injection, response serialization,
and translation of application exceptions.

Authentication workflows remain in the Service Layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies.database import DatabaseSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import auth_service


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
    description=(
        "Authenticate a user with username and password "
        "and return a signed JWT access token."
    ),
)
async def login(
    credentials: LoginRequest,
    db: DatabaseSession,
) -> TokenResponse:
    """
    Authenticate a user and return an access token.
    """

    access_token = await auth_service.login(
        db,
        username=credentials.username,
        password=credentials.password,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


__all__ = [
    "router",
    "login",
]