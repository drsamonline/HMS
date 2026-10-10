"""
HHMS Inventory Item Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.inventory_item import InventoryItem
from app.repositories.inventory_item import (
    InventoryItemRepository,
    inventory_item_repository,
)
from app.schemas.inventory_item import (
    InventoryItemCreate,
    InventoryItemUpdate,
)


class InventoryItemService:
    """Business operations for general inventory items."""

    def __init__(
        self,
        repository: InventoryItemRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            or inventory_item_repository
        )

    async def get(
        self,
        db: AsyncSession,
        item_id: int,
    ) -> InventoryItem:
        item = await self.repository.get_by_id(
            db,
            item_id,
        )

        if item is None:
            raise ResourceNotFoundException(
                "Inventory item not found."
            )

        return item

    async def list(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryItem]:
        return await self.repository.list_items(
            db,
            search=search,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        data: InventoryItemCreate,
    ) -> InventoryItem:
        existing = (
            await self.repository.get_by_code(
                db,
                data.item_code,
            )
        )

        if existing is not None:
            raise DuplicateResourceException(
                "Inventory item code already exists."
            )

        now = datetime.now(timezone.utc)

        item = InventoryItem(
            **data.model_dump(),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        try:
            item = await self.repository.add(
                db,
                item,
            )

            await db.commit()

            return item

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Inventory item code already exists."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create inventory item."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        *,
        item_id: int,
        data: InventoryItemUpdate,
    ) -> InventoryItem:
        item = await self.get(
            db,
            item_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        for field, value in values.items():
            setattr(
                item,
                field,
                value,
            )

        item.updated_at = (
            datetime.now(timezone.utc)
        )

        try:
            item = await self.repository.update(
                db,
                item,
            )

            await db.commit()

            return item

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update inventory item."
            ) from exc


inventory_item_service = (
    InventoryItemService()
)


__all__ = [
    "InventoryItemService",
    "inventory_item_service",
]