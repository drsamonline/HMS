"""
CRUD operations for the Permission model.

Extends the generic CRUDBase with permission-specific queries.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.permission import Permission
from app.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
)


class PermissionCRUD(
    CRUDBase[
        Permission,
        PermissionCreate,
        PermissionUpdate,
    ]
):
    """
    CRUD operations for Permission entities.
    """

    def __init__(self) -> None:
        super().__init__(Permission)

    async def get_by_code(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> Permission | None:
        """
        Retrieve a permission by its unique code.

        Args:
            db:
                Active database session.
            code:
                Unique permission code.

        Returns:
            Matching permission if found; otherwise None.
        """
        result = await db.execute(
            select(Permission).where(
                Permission.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        name: str,
    ) -> Permission | None:
        """
        Retrieve a permission by its display name.

        Args:
            db:
                Active database session.
            name:
                Permission display name.

        Returns:
            Matching permission if found; otherwise None.
        """
        result = await db.execute(
            select(Permission).where(
                Permission.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_module(
        self,
        db: AsyncSession,
        *,
        module: str,
    ) -> list[Permission]:
        """
        Retrieve all permissions belonging to a module.

        Args:
            db:
                Active database session.
            module:
                Module name.

        Returns:
            List of matching permissions.
        """
        result = await db.execute(
            select(Permission)
            .where(Permission.module == module)
            .order_by(Permission.code)
        )

        return list(result.scalars().all())


permission_crud = PermissionCRUD()

__all__ = [
    "PermissionCRUD",
    "permission_crud",
]