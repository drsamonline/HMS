"""
HHMS Inventory Item Service.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleException,
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
    """Business operations for pharmacy inventory items."""

    def __init__(
        self,
        repository: InventoryItemRepository | None = None,
    ) -> None:
        self.repository = (
            repository or inventory_item_repository
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
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryItem]:
        return await self.repository.list_items(
            db,
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
            await self.repository.get_by_medicine(
                db,
                data.medicine_id,
            )
        )

        if existing is not None:
            raise DuplicateResourceException(
                "An inventory item already exists "
                "for this medicine."
            )

        if (
            data.maximum_quantity is not None
            and data.maximum_quantity
            < data.minimum_quantity
        ):
            raise BusinessRuleException(
                "Maximum quantity cannot be less "
                "than minimum quantity."
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
                "Unable to create inventory item."
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

        minimum = values.get(
            "minimum_quantity",
            item.minimum_quantity,
        )

        maximum = values.get(
            "maximum_quantity",
            item.maximum_quantity,
        )

        if (
            maximum is not None
            and maximum < minimum
        ):
            raise BusinessRuleException(
                "Maximum quantity cannot be less "
                "than minimum quantity."
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


inventory_item_service = InventoryItemService()


__all__ = [
    "InventoryItemService",
    "inventory_item_service",
]