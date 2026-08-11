"""
HHMS Stock Transaction Service.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleException,
    DatabaseException,
    ResourceNotFoundException,
)
from app.models.inventory_item import InventoryItem
from app.models.stock_transaction import StockTransaction
from app.repositories.stock_transaction import (
    StockTransactionRepository,
    stock_transaction_repository,
)
from app.schemas.stock_transaction import (
    StockTransactionCreate,
)


class StockTransactionService:
    """Business operations for inventory movements."""

    def __init__(
        self,
        repository: StockTransactionRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            or stock_transaction_repository
        )

    async def get(
        self,
        db: AsyncSession,
        transaction_id: int,
    ) -> StockTransaction:
        transaction = (
            await self.repository.get_by_id(
                db,
                transaction_id,
            )
        )

        if transaction is None:
            raise ResourceNotFoundException(
                "Stock transaction not found."
            )

        return transaction

    async def list_by_inventory_item(
        self,
        db: AsyncSession,
        *,
        inventory_item_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[StockTransaction]:
        return await (
            self.repository.list_by_inventory_item(
                db,
                inventory_item_id=inventory_item_id,
                skip=skip,
                limit=limit,
            )
        )

    async def create(
        self,
        db: AsyncSession,
        data: StockTransactionCreate,
    ) -> StockTransaction:
        item = await db.get(
            InventoryItem,
            data.inventory_item_id,
        )

        if item is None:
            raise ResourceNotFoundException(
                "Inventory item not found."
            )

        if not item.is_active:
            raise BusinessRuleException(
                "Cannot record stock movement for "
                "an inactive inventory item."
            )

        now = datetime.now(timezone.utc)

        transaction = StockTransaction(
            inventory_item_id=data.inventory_item_id,
            transaction_type=data.transaction_type,
            quantity=data.quantity,
            reference_number=data.reference_number,
            transaction_datetime=now,
            performed_by=data.performed_by,
            remarks=data.remarks,
            created_at=now,
            updated_at=now,
        )

        try:
            transaction = (
                await self.repository.add(
                    db,
                    transaction,
                )
            )

            await db.commit()

            return transaction

        except IntegrityError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create stock transaction."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create stock transaction."
            ) from exc


stock_transaction_service = (
    StockTransactionService()
)


__all__ = [
    "StockTransactionService",
    "stock_transaction_service",
]