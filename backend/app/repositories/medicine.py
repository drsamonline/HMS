"""
HHMS Medicine Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medicine import Medicine
from app.repositories.base import RepositoryBase


class MedicineRepository(RepositoryBase[Medicine]):
    """Persistence operations for medicines."""

    def __init__(self) -> None:
        super().__init__(Medicine)

    async def get_by_id(
        self,
        db: AsyncSession,
        medicine_id: int,
    ) -> Medicine | None:
        return await db.get(
            Medicine,
            medicine_id,
        )

    async def get_by_code(
        self,
        db: AsyncSession,
        medicine_code: str,
    ) -> Medicine | None:
        result = await db.execute(
            select(Medicine).where(
                Medicine.medicine_code == medicine_code,
            )
        )

        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Medicine]:
        statement = select(Medicine)

        if active_only:
            statement = statement.where(
                Medicine.is_active.is_(True)
            )

        if search:
            term = f"%{search.strip()}%"

            statement = statement.where(
                Medicine.medicine_name.ilike(term)
                | Medicine.medicine_code.ilike(term)
                | Medicine.scientific_name.ilike(term)
            )

        result = await db.execute(
            statement
            .order_by(Medicine.medicine_name.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())


medicine_repository = MedicineRepository()


__all__ = [
    "MedicineRepository",
    "medicine_repository",
]