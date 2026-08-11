"""
HHMS Role Repository
====================

Database-access operations specific to the Role entity.

Repositories contain persistence queries only. Business rules,
authorization, validation workflows, and orchestration belong
to the Service Layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.repositories.base import RepositoryBase


class RoleRepository(
    RepositoryBase[Role],
):
    """
    Repository for Role database operations.
    """

    def __init__(self) -> None:
        """
        Initialize the Role repository.
        """

        super().__init__(Role)

    async def get_by_code(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> Role | None:
        """
        Retrieve a role by its unique code.

        Role code normalization and validation are intentionally
        handled outside the repository.
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

        Role name normalization and validation are intentionally
        handled outside the repository.
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

        return list(
            result.scalars().all()
        )


role_repository = RoleRepository()


__all__ = [
    "RoleRepository",
    "role_repository",
]