"""
HHMS Stock Transaction Service.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
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
    """
    Business operations for the Simple Stock Register.

    Stock transactions are treated as immutable ledger records.
    """

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

    async def list_by_item(
        self,
        db: AsyncSession,
        inventory_item_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[StockTransaction]:
        item = await db.get(
            InventoryItem,
            inventory_item_id,
        )

        if item is None:
            raise ResourceNotFoundException(
                "Inventory item not found."
            )

        return await self.repository.list_by_item(
            db,
            inventory_item_id,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        data: StockTransactionCreate,
        performed_by: int,
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
                "Cannot create a stock transaction "
                "for an inactive inventory item."
            )

        if performed_by <= 0:
            raise BusinessRuleException(
                "Invalid performing user."
            )

        if data.quantity == 0:
            raise BusinessRuleException(
                "Transaction quantity cannot be zero."
            )

        if (
            data.transaction_type
            != "Adjustment"
            and data.quantity < 0
        ):
            raise BusinessRuleException(
                "Receipt, Issue and Return quantities "
                "must be positive."
            )

        now = datetime.now(timezone.utc)

        transaction = StockTransaction(
            inventory_item_id=data.inventory_item_id,
            transaction_type=data.transaction_type,
            quantity=data.quantity,
            reference_number=data.reference_number,
            transaction_datetime=(
                data.transaction_datetime
                or now
            ),
            performed_by=performed_by,
            remarks=data.remarks,
            created_at=now,
            updated_at=now,
        )

        try:
            db.add(transaction)

            await db.commit()
            await db.refresh(transaction)

            return transaction

        except IntegrityError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create stock transaction "
                "because a referenced record is invalid."
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