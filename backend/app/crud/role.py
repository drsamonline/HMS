"""
CRUD operations for the Role model.

Extends the generic CRUDBase with role-specific queries.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.role import Role
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
)


class RoleCRUD(
    CRUDBase[
        Role,
        RoleCreate,
        RoleUpdate,
    ]
):
    """
    CRUD operations for Role entities.
    """

    def __init__(self) -> None:
        super().__init__(Role)

    async def get_by_code(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> Role | None:
        """
        Retrieve a role by its unique code.
        """

        result = await db.execute(
            select(Role).where(
                Role.code == code,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        name: str,
    ) -> Role | None:
        """
        Retrieve a role by its unique name.
        """

        result = await db.execute(
            select(Role).where(
                Role.name == name,
            )
        )

        return result.scalar_one_or_none()

    async def get_active(
        self,
        db: AsyncSession,
    ) -> list[Role]:
        """
        Retrieve all active roles ordered by name.
        """

        result = await db.execute(
            select(Role)
            .where(Role.is_active.is_(True))
            .order_by(Role.name)
        )

        return list(result.scalars().all())


role_crud = RoleCRUD()


__all__ = [
    "RoleCRUD",
    "role_crud",
]