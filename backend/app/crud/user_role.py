"""
CRUD operations for the RolePermission model.

Provides persistence operations specific to role-permission
assignments. Business rules belong in the service layer.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.role_permission import RolePermission
from app.schemas.role_permission import RolePermissionCreate


class RolePermissionCRUD(
    CRUDBase[
        RolePermission,
        RolePermissionCreate,
        RolePermissionCreate,
    ]
):
    """
    CRUD implementation for RolePermission entities.
    """

    def __init__(self) -> None:
        super().__init__(RolePermission)

    async def get_by_role(
        self,
        db: AsyncSession,
        *,
        role_id: UUID,
    ) -> list[RolePermission]:
        """
        Return all permissions assigned to a role.
        """
        result = await db.execute(
            select(RolePermission)
            .where(RolePermission.role_id == role_id)
            .order_by(RolePermission.permission_id)
        )

        return list(result.scalars())

    async def get_by_permission(
        self,
        db: AsyncSession,
        *,
        permission_id: UUID,
    ) -> list[RolePermission]:
        """
        Return all roles assigned to a permission.
        """
        result = await db.execute(
            select(RolePermission)
            .where(RolePermission.permission_id == permission_id)
            .order_by(RolePermission.role_id)
        )

        return list(result.scalars())

    async def exists(
        self,
        db: AsyncSession,
        *,
        role_id: UUID,
        permission_id: UUID,
    ) -> bool:
        """
        Determine whether a role already has the specified permission.
        """
        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )

        return result.scalar_one_or_none() is not None


role_permission_crud = RolePermissionCRUD()

__all__ = [
    "RolePermissionCRUD",
    "role_permission_crud",
]