"""Persistence operations for the pharmacy batch stock ledger."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stock_card import StockCard
from app.repositories.base import RepositoryBase


class StockCardRepository(RepositoryBase[StockCard]):
    def __init__(self) -> None:
        super().__init__(StockCard)

    async def list_by_batch(self, db: AsyncSession, stock_batch_id: int, *, skip: int = 0, limit: int = 200) -> list[StockCard]:
        result = await db.execute(
            select(StockCard)
            .where(StockCard.stock_batch_id == stock_batch_id)
            .order_by(StockCard.transaction_datetime.desc(), StockCard.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


stock_card_repository = StockCardRepository()
__all__ = ["StockCardRepository", "stock_card_repository"]
