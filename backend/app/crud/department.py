"""
CRUD operations for the Department model.

Provides persistence operations specific to hospital
departments. Business rules belong in the service layer.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.department import Department
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
)


class DepartmentCRUD(
    CRUDBase[
        Department,
        DepartmentCreate,
        DepartmentUpdate,
    ]
):
    """
    CRUD implementation for Department entities.
    """

    def __init__(self) -> None:
        super().__init__(Department)

    async def get_by_code(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> Department | None:
        """
        Retrieve a department by its business code.
        """
        result = await db.execute(
            select(Department).where(
                Department.code == code,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        name: str,
    ) -> Department | None:
        """
        Retrieve a department by its name.
        """
        result = await db.execute(
            select(Department).where(
                Department.name == name,
            )
        )

        return result.scalar_one_or_none()

    async def exists_code(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> bool:
        """
        Check whether a department code already exists.
        """
        return await self.get_by_code(
            db,
            code=code,
        ) is not None

    async def exists_name(
        self,
        db: AsyncSession,
        *,
        name: str,
    ) -> bool:
        """
        Check whether a department name already exists.
        """
        return await self.get_by_name(
            db,
            name=name,
        ) is not None


department_crud = DepartmentCRUD()

__all__ = [
    "DepartmentCRUD",
    "department_crud",
]