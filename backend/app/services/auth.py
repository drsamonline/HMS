"""
HHMS Authentication Service
===========================

Application-level authentication workflows for HHMS.

This module coordinates user lookup, password verification, and JWT
access-token creation. Database queries remain in the User Repository,
and HTTP concerns remain in the API layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Final

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.core.exceptions import (
    AuthenticationException,
    DatabaseException,
)
from app.models.user import User
from app.services.user import UserService


_INVALID_CREDENTIALS_MESSAGE: Final[str] = (
    "Incorrect username or password."
)


class AuthService:
    """
    Service layer for authentication workflows.

    The service deliberately does not depend on FastAPI request objects,
    OAuth2 dependencies, or HTTP response classes.
    """

    def __init__(
        self,
        user_service: UserService | None = None,
    ) -> None:
        """
        Initialize the Authentication Service.

        Parameters
        ----------
        user_service : UserService | None
            Optional user-service instance. When omitted, the shared
            application UserService is used.
        """

        self.user_service = user_service or UserService()

    async def authenticate(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
    ) -> User:
        """
        Authenticate a user by username and plaintext password.

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        username : str
            Login username.

        password : str
            Plaintext password supplied by the caller.

        Returns
        -------
        User
            Authenticated user entity.

        Raises
        ------
        AuthenticationException
            If the username does not exist or the password is invalid.

        DatabaseException
            If the user lookup fails because of a database error.
        """

        normalized_username = username.strip()

        if not normalized_username or not password:
            raise AuthenticationException(
                _INVALID_CREDENTIALS_MESSAGE
            )

        try:
            user = await self.user_service.get_by_username(
                db,
                username=normalized_username,
            )

        except SQLAlchemyError as exc:
            raise DatabaseException(
                "Unable to authenticate user."
            ) from exc

        if user is None:
            raise AuthenticationException(
                _INVALID_CREDENTIALS_MESSAGE
            )

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise AuthenticationException(
                _INVALID_CREDENTIALS_MESSAGE
            )

        return user

    async def login(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
    ) -> str:
        """
        Authenticate a user and issue a JWT access token.

        The user's immutable UUID is used as the JWT subject so that
        token identity does not depend on a mutable username.

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        username : str
            Login username.

        password : str
            Plaintext password supplied by the caller.

        Returns
        -------
        str
            Signed JWT access token.
        """

        user = await self.authenticate(
            db,
            username=username,
            password=password,
        )

        return create_access_token(
            subject=str(user.id),
        )


auth_service = AuthService()


__all__ = [
    "AuthService",
    "auth_service",
]