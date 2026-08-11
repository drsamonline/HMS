"""
CRUD operations for the UserRole model.

Provides persistence operations specific to user-role
assignments. Business rules belong in the service layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user_role import UserRole
from app.schemas.user_role import UserRoleCreate


class UserRoleCRUD(
    CRUDBase[
        UserRole,
        UserRoleCreate,
        UserRoleCreate,
    ]
):
    """
    CRUD implementation for UserRole entities.
    """

    def __init__(self) -> None:
        super().__init__(UserRole)

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> list[UserRole]:
        """
        Return all roles assigned to a user.
        """
        result = await db.execute(
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .order_by(UserRole.role_id)
        )

        return list(result.scalars().all())

    async def get_by_role(
        self,
        db: AsyncSession,
        *,
        role_id: UUID,
    ) -> list[UserRole]:
        """
        Return all users assigned to a role.
        """
        result = await db.execute(
            select(UserRole)
            .where(UserRole.role_id == role_id)
            .order_by(UserRole.user_id)
        )

        return list(result.scalars().all())

    async def exists(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        role_id: UUID,
    ) -> bool:
        """
        Determine whether a user already has the specified role.
        """
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )

        return result.scalar_one_or_none() is not None


user_role_crud = UserRoleCRUD()

__all__ = [
    "UserRoleCRUD",
    "user_role_crud",
]