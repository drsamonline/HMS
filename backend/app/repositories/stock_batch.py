"""
HHMS Stock Batch Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_batch import StockBatch
from app.repositories.base import RepositoryBase


class StockBatchRepository(RepositoryBase[StockBatch]):
    """Persistence operations for stock batches."""

    def __init__(self) -> None:
        super().__init__(StockBatch)

    async def get_by_id(
        self,
        db: AsyncSession,
        stock_batch_id: int,
    ) -> StockBatch | None:
        return await db.get(
            StockBatch,
            stock_batch_id,
        )

    async def list_by_medicine(
        self,
        db: AsyncSession,
        medicine_id: int,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[StockBatch]:
        statement = select(StockBatch).where(
            StockBatch.medicine_id == medicine_id,
        )

        if active_only:
            statement = statement.where(
                StockBatch.is_active.is_(True),
            )

        result = await db.execute(
            statement
            .order_by(
                StockBatch.expiry_date.asc().nullslast(),
                StockBatch.id.asc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def list_available(
        self,
        db: AsyncSession,
        medicine_id: int,
    ) -> list[StockBatch]:
        result = await db.execute(
            select(StockBatch)
            .where(
                StockBatch.medicine_id == medicine_id,
                StockBatch.quantity_remaining > 0,
                StockBatch.is_active.is_(True),
            )
            .order_by(
                StockBatch.expiry_date.asc().nullslast(),
                StockBatch.id.asc(),
            )
        )

        return list(result.scalars().all())


stock_batch_repository = StockBatchRepository()


__all__ = [
    "StockBatchRepository",
    "stock_batch_repository",
]