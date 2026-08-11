"""
HHMS Inventory Item Repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_item import InventoryItem
from app.repositories.base import RepositoryBase


class InventoryItemRepository(
    RepositoryBase[InventoryItem],
):
    """Persistence operations for inventory items."""

    def __init__(self) -> None:
        super().__init__(InventoryItem)

    async def get_by_id(
        self,
        db: AsyncSession,
        item_id: int,
    ) -> InventoryItem | None:
        return await db.get(
            InventoryItem,
            item_id,
        )

    async def get_by_medicine(
        self,
        db: AsyncSession,
        medicine_id: int,
    ) -> InventoryItem | None:
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.medicine_id == medicine_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_items(
        self,
        db: AsyncSession,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryItem]:
        statement = select(InventoryItem)

        if active_only:
            statement = statement.where(
                InventoryItem.is_active.is_(True),
            )

        result = await db.execute(
            statement
            .order_by(InventoryItem.id.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())


inventory_item_repository = InventoryItemRepository()


__all__ = [
    "InventoryItemRepository",
    "inventory_item_repository",
]