"""
CRUD operations for the Designation model.

Provides persistence operations specific to staff
designations. Business rules belong in the service layer.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.designation import Designation
from app.schemas.designation import (
    DesignationCreate,
    DesignationUpdate,
)


class DesignationCRUD(
    CRUDBase[
        Designation,
        DesignationCreate,
        DesignationUpdate,
    ]
):
    """
    CRUD implementation for Designation entities.
    """

    def __init__(self) -> None:
        super().__init__(Designation)

    async def get_by_code(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> Designation | None:
        """
        Retrieve a designation by its business code.
        """
        result = await db.execute(
            select(Designation).where(
                Designation.code == code,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        name: str,
    ) -> Designation | None:
        """
        Retrieve a designation by its name.
        """
        result = await db.execute(
            select(Designation).where(
                Designation.name == name,
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
        Check whether a designation code already exists.
        """
        return (
            await self.get_by_code(
                db,
                code=code,
            )
            is not None
        )

    async def exists_name(
        self,
        db: AsyncSession,
        *,
        name: str,
    ) -> bool:
        """
        Check whether a designation name already exists.
        """
        return (
            await self.get_by_name(
                db,
                name=name,
            )
            is not None
        )


designation_crud = DesignationCRUD()

__all__ = [
    "DesignationCRUD",
    "designation_crud",
]