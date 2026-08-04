"""
User-specific CRUD operations for HHMS.

Extends the generic CRUDBase with user-specific queries.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserCRUD(
    CRUDBase[
        User,
        UserCreate,
        UserUpdate,
    ]
):
    """
    CRUD operations for User entities.
    """

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_username(
        self,
        db: AsyncSession,
        *,
        username: str,
    ) -> User | None:
        """
        Retrieve a user by username.
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        db: AsyncSession,
        *,
        email: str,
    ) -> User | None:
        """
        Retrieve a user by email.
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


user_crud = UserCRUD()

__all__ = [
    "UserCRUD",
    "user_crud",
]