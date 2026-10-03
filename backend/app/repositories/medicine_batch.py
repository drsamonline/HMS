"""
HHMS Medicine Batch Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medicine_batch import MedicineBatch
from app.repositories.base import RepositoryBase


class MedicineBatchRepository(
    RepositoryBase[MedicineBatch],
):
    """Persistence operations for medicine batches."""

    def __init__(self) -> None:
        super().__init__(MedicineBatch)

    async def get_by_id(
        self,
        db: AsyncSession,
        batch_id: int,
    ) -> MedicineBatch | None:
        return await db.get(
            MedicineBatch,
            batch_id,
        )

    async def get_by_batch_number(
        self,
        db: AsyncSession,
        *,
        medicine_id: int,
        batch_number: str,
    ) -> MedicineBatch | None:
        result = await db.execute(
            select(MedicineBatch).where(
                MedicineBatch.medicine_id == medicine_id,
                MedicineBatch.batch_number == batch_number,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_medicine(
        self,
        db: AsyncSession,
        *,
        medicine_id: int,
        active_only: bool = True,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[MedicineBatch]:
        statement = select(MedicineBatch).where(
            MedicineBatch.medicine_id == medicine_id,
        )

        if active_only:
            statement = statement.where(
                MedicineBatch.is_active.is_(True),
            )

        if available_only:
            statement = statement.where(
                MedicineBatch.quantity_in_stock > 0,
            )

        result = await db.execute(
            statement
            .order_by(
                MedicineBatch.expiry_date.asc().nullslast(),
                MedicineBatch.id.asc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )


medicine_batch_repository = MedicineBatchRepository()


__all__ = [
    "MedicineBatchRepository",
    "medicine_batch_repository",
]