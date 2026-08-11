"""
HHMS Stock Transaction Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_transaction import StockTransaction
from app.repositories.base import RepositoryBase


class StockTransactionRepository(
    RepositoryBase[StockTransaction],
):
    """Persistence operations for stock transactions."""

    def __init__(self) -> None:
        super().__init__(StockTransaction)

    async def get_by_id(
        self,
        db: AsyncSession,
        transaction_id: int,
    ) -> StockTransaction | None:
        return await db.get(
            StockTransaction,
            transaction_id,
        )

    async def list_by_inventory_item(
        self,
        db: AsyncSession,
        *,
        inventory_item_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[StockTransaction]:
        result = await db.execute(
            select(StockTransaction)
            .where(
                StockTransaction.inventory_item_id
                == inventory_item_id,
            )
            .order_by(
                StockTransaction.transaction_datetime.desc(),
                StockTransaction.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())


stock_transaction_repository = (
    StockTransactionRepository()
)


__all__ = [
    "StockTransactionRepository",
    "stock_transaction_repository",
]