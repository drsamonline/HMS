"""
HHMS Stock Batch Service.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from app.models.stock_batch import StockBatch
from app.repositories.stock_batch import (
    StockBatchRepository,
    stock_batch_repository,
)
from app.schemas.stock_batch import (
    StockBatchCreate,
    StockBatchUpdate,
)


class StockBatchService:
    """Business operations for batch-wise medicine stock."""

    def __init__(
        self,
        repository: StockBatchRepository | None = None,
    ) -> None:
        self.repository = (
            repository or stock_batch_repository
        )

    async def get(
        self,
        db: AsyncSession,
        stock_batch_id: int,
    ) -> StockBatch:
        batch = await self.repository.get_by_id(
            db,
            stock_batch_id,
        )

        if batch is None:
            raise ResourceNotFoundException(
                "Stock batch not found."
            )

        return batch

    async def list_by_medicine(
        self,
        db: AsyncSession,
        medicine_id: int,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[StockBatch]:
        return await self.repository.list_by_medicine(
            db,
            medicine_id,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )

    async def create(
        self,
        db: AsyncSession,
        data: StockBatchCreate,
    ) -> StockBatch:
        now = datetime.now(timezone.utc)

        total_cost = (
            data.quantity_received * data.unit_cost
        )

        batch = StockBatch(
            medicine_id=data.medicine_id,
            batch_no=data.batch_no,
            expiry_date=data.expiry_date,
            manufacture_date=data.manufacture_date,
            quantity_received=data.quantity_received,
            quantity_remaining=data.quantity_received,
            unit_cost=data.unit_cost,
            total_cost=total_cost,
            supplier_id=data.supplier_id,
            goods_receipt_id=data.goods_receipt_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        try:
            db.add(batch)
            await db.commit()
            await db.refresh(batch)

            return batch

        except IntegrityError as exc:
            await db.rollback()

            raise DuplicateResourceException(
                "Unable to create stock batch because "
                "a referenced record is invalid or duplicated."
            ) from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to create stock batch."
            ) from exc

    async def update(
        self,
        db: AsyncSession,
        stock_batch_id: int,
        data: StockBatchUpdate,
    ) -> StockBatch:
        batch = await self.get(
            db,
            stock_batch_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        for field, value in values.items():
            setattr(
                batch,
                field,
                value,
            )

        batch.updated_at = (
            datetime.now(timezone.utc)
        )

        try:
            await db.commit()
            await db.refresh(batch)

            return batch

        except SQLAlchemyError as exc:
            await db.rollback()

            raise DatabaseException(
                "Unable to update stock batch."
            ) from exc


stock_batch_service = StockBatchService()


__all__ = [
    "StockBatchService",
    "stock_batch_service",
]