"""
HHMS User Service
=================

Business and application workflows for User entities.

The User Service coordinates validation, duplicate detection,
password preparation, repository operations, and transaction
boundaries.

Database queries belong to the Repository Layer.
Password cryptography belongs to the Core Security Layer.
HTTP concerns belong to the API Layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """
    Service layer for User business workflows.
    """

    def __init__(
        self,
        repository: UserRepository | None = None,
    ) -> None:
        """
        Initialize the User Service.

        Parameters
        ----------
        repository : UserRepository | None
            Optional repository instance. The default uses the
            application's shared User repository.
        """

        self.repository = repository or UserRepository()

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> User:
        """
        Retrieve a user by primary key.

        Raises
        ------
        ResourceNotFoundException
            If the user does not exist.
        """

        user = await self.repository.get(
            db,
            user_id,
        )

        if user is None:
            raise ResourceNotFoundException(
                "User not found."
            )

        return user

    async def get_by_username(
        self,
        db: AsyncSession,
        *,
        username: str,
    ) -> User | None:
        """
        Retrieve a user by username.

        Username normalization is performed before querying.
        """

        normalized_username = username.strip()

        if not normalized_username:
            return None

        return await self.repository.get_by_username(
            db,
            username=normalized_username,
        )

    async def get_by_email(
        self,
        db: AsyncSession,
        *,
        email: str,
    ) -> User | None:
        """
        Retrieve a user by email address.

        Email normalization is performed before querying.
        """

        normalized_email = email.strip().lower()

        if not normalized_email:
            return None

        return await self.repository.get_by_email(
            db,
            email=normalized_email,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        user_in: UserCreate,
    ) -> User:
        """
        Create a new user.

        Duplicate usernames and email addresses are rejected.
        The plaintext password is converted to a secure hash
        before persistence.

        The service owns the transaction boundary.
        """

        username = user_in.username.strip()
        email = user_in.email.strip().lower()

        existing_username = (
            await self.repository.get_by_username(
                db,
                username=username,
            )
        )

        if existing_username is not None:
            raise DuplicateResourceException(
                "Username is already registered."
            )

        existing_email = (
            await self.repository.get_by_email(
                db,
                email=email,
            )
        )

        if existing_email is not None:
            raise DuplicateResourceException(
                "Email address is already registered."
            )

        user = User(
            username=username,
            email=email,
            full_name=user_in.full_name.strip(),
            hashed_password=hash_password(
                user_in.password,
            ),
        )

        try:
            user = await self.repository.add(
                db,
                user,
            )

            await db.commit()

            return user

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "User with the supplied username or email already exists."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create user."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        user_in: UserUpdate,
    ) -> User:
        """
        Update an existing user.

        Password changes are hashed before persistence.
        Username and email uniqueness is checked before update.

        The ``is_superuser`` privilege is intentionally not
        modified by this service method.
        """

        user = await self.get_by_id(
            db,
            user_id=user_id,
        )

        update_data = user_in.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            return user

        if "username" in update_data:
            username = update_data["username"].strip()

            existing_username = (
                await self.repository.get_by_username(
                    db,
                    username=username,
                )
            )

            if (
                existing_username is not None
                and existing_username.id != user.id
            ):
                raise DuplicateResourceException(
                    "Username is already registered."
                )

            update_data["username"] = username

        if "email" in update_data:
            email = update_data["email"].strip().lower()

            existing_email = (
                await self.repository.get_by_email(
                    db,
                    email=email,
                )
            )

            if (
                existing_email is not None
                and existing_email.id != user.id
            ):
                raise DuplicateResourceException(
                    "Email address is already registered."
                )

            update_data["email"] = email

        if "full_name" in update_data:
            update_data["full_name"] = (
                update_data["full_name"].strip()
            )

        if "password" in update_data:
            update_data["hashed_password"] = (
                hash_password(
                    update_data.pop("password")
                )
            )

        try:
            for field, value in update_data.items():
                setattr(
                    user,
                    field,
                    value,
                )

            user = await self.repository.update(
                db,
                user,
            )

            await db.commit()

            return user

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "User with the supplied username or email already exists."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update user."
            ) from exc

    async def delete(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> None:
        """
        Delete an existing user.

        The operation is a hard delete. Soft-deletion policy,
        where required by a future module, must be explicitly
        implemented rather than silently changing generic behavior.
        """

        user = await self.get_by_id(
            db,
            user_id=user_id,
        )

        try:
            await self.repository.delete(
                db,
                user,
            )

            await db.commit()

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to delete user."
            ) from exc


user_service = UserService()


__all__ = [
    "UserService",
    "user_service",
]