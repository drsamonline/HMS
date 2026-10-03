"""
HHMS User Repository
====================

Database-access operations specific to the User entity.

This module contains persistence queries only. Authentication,
password handling, authorization, validation, and business rules
belong to the Service Layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import RepositoryBase


class UserRepository(
    RepositoryBase[User],
):
    """
    Repository for User database operations.
    """

    def __init__(self) -> None:
        """
        Initialize the User repository.
        """

        super().__init__(User)

    async def get_by_username(
        self,
        db: AsyncSession,
        *,
        username: str,
    ) -> User | None:
        """
        Retrieve a user by username.

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        username : str
            Username to search for.

        Returns
        -------
        User | None
            Matching user or None when no record exists.

        Notes
        -----
        Username normalization and validation are intentionally
        handled outside the repository.
        """

        result = await db.execute(
            select(User).where(
                User.username == username,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        db: AsyncSession,
        *,
        email: str,
    ) -> User | None:
        """
        Retrieve a user by email address.

        Parameters
        ----------
        db : AsyncSession
            Active asynchronous database session.

        email : str
            Email address to search for.

        Returns
        -------
        User | None
            Matching user or None when no record exists.

        Notes
        -----
        Email normalization and validation are intentionally
        handled outside the repository.
        """

        result = await db.execute(
            select(User).where(
                User.email == email,
            )
        )

        return result.scalar_one_or_none()


user_repository = UserRepository()


__all__ = [
    "UserRepository",
    "user_repository",
]