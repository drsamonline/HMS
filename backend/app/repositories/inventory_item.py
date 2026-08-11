"""
HHMS Inventory Item Repository.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
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
        super().__init__(
            InventoryItem,
        )

    async def get_by_id(
        self,
        db: AsyncSession,
        item_id: int,
    ) -> InventoryItem | None:
        return await db.get(
            InventoryItem,
            item_id,
        )

    async def get_by_code(
        self,
        db: AsyncSession,
        item_code: str,
    ) -> InventoryItem | None:
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.item_code == item_code,
            )
        )

        return result.scalar_one_or_none()

    async def list_items(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryItem]:
        statement = select(
            InventoryItem,
        )

        if search:
            pattern = f"%{search}%"

            statement = statement.where(
                (
                    InventoryItem.item_code.ilike(
                        pattern
                    )
                    |
                    InventoryItem.item_name.ilike(
                        pattern
                    )
                    |
                    InventoryItem.category.ilike(
                        pattern
                    )
                )
            )

        if active_only:
            statement = statement.where(
                InventoryItem.is_active.is_(True),
            )

        result = await db.execute(
            statement
            .order_by(
                InventoryItem.item_name.asc(),
                InventoryItem.id.asc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )


inventory_item_repository = (
    InventoryItemRepository()
)


__all__ = [
    "InventoryItemRepository",
    "inventory_item_repository",
]