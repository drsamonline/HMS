"""Business service for atomic pharmacy stock movements and stock cards."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BusinessRuleException, DatabaseException, ResourceNotFoundException
from app.models.stock_batch import StockBatch
from app.models.stock_card import StockCard
from app.repositories.stock_card import StockCardRepository, stock_card_repository
from app.schemas.stock_card import StockCardCreate


class StockCardService:
    def __init__(self, repository: StockCardRepository | None = None) -> None:
        self.repository = repository or stock_card_repository

    async def list_by_batch(self, db: AsyncSession, stock_batch_id: int, *, skip: int = 0, limit: int = 200) -> list[StockCard]:
        batch = await db.get(StockBatch, stock_batch_id)
        if batch is None:
            raise ResourceNotFoundException("Stock batch not found.")
        return await self.repository.list_by_batch(db, stock_batch_id, skip=skip, limit=limit)

    async def create(self, db: AsyncSession, stock_batch_id: int, data: StockCardCreate, created_by: int) -> StockCard:
        batch = await db.get(StockBatch, stock_batch_id)
        if batch is None:
            raise ResourceNotFoundException("Stock batch not found.")
        if not batch.is_active:
            raise BusinessRuleException("Cannot move stock from an inactive batch.")
        if created_by <= 0:
            raise BusinessRuleException("Invalid performing user.")
        qty = Decimal(data.quantity)
        if qty <= 0:
            raise BusinessRuleException("Stock movement quantity must be greater than zero.")

        if data.transaction_type in {"Receipt", "Return"}:
            delta = qty
        elif data.transaction_type == "Issue":
            delta = -qty
        else:
            raise BusinessRuleException("Manual adjustment requires a dedicated signed adjustment endpoint.")

        new_balance = Decimal(batch.quantity_remaining) + delta
        if new_balance < 0:
            raise BusinessRuleException("Insufficient stock in the selected batch.")

        now = datetime.now(timezone.utc)
        quantity_in = qty if delta > 0 else Decimal("0")
        quantity_out = qty if delta < 0 else Decimal("0")
        try:
            result = await db.execute(
                update(StockBatch)
                .where(
                    StockBatch.id == stock_batch_id,
                    StockBatch.is_active.is_(True),
                    StockBatch.quantity_remaining + delta >= 0,
                )
                .values(quantity_remaining=new_balance, updated_at=now)
            )
            if result.rowcount != 1:
                raise BusinessRuleException("Stock balance changed before this transaction could be applied.")

            card = StockCard(
                medicine_id=batch.medicine_id,
                stock_batch_id=batch.id,
                transaction_type=data.transaction_type,
                quantity_in=quantity_in,
                quantity_out=quantity_out,
                balance_quantity=new_balance,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                transaction_datetime=data.transaction_datetime or now,
                created_by=created_by,
                remarks=data.remarks,
                created_at=now,
            )
            db.add(card)
            await db.commit()
            await db.refresh(card)
            return card
        except BusinessRuleException:
            await db.rollback()
            raise
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to record pharmacy stock movement.") from exc

    async def create_adjustment(self, db: AsyncSession, stock_batch_id: int, quantity_delta: Decimal, *, created_by: int, reference_type: str | None = None, reference_id: int | None = None, remarks: str | None = None) -> StockCard:
        batch = await db.get(StockBatch, stock_batch_id)
        if batch is None:
            raise ResourceNotFoundException("Stock batch not found.")
        if not batch.is_active:
            raise BusinessRuleException("Cannot adjust an inactive stock batch.")
        if quantity_delta == 0:
            raise BusinessRuleException("Adjustment quantity cannot be zero.")
        new_balance = Decimal(batch.quantity_remaining) + Decimal(quantity_delta)
        if new_balance < 0:
            raise BusinessRuleException("Adjustment would make stock negative.")
        now = datetime.now(timezone.utc)
        try:
            result = await db.execute(
                update(StockBatch)
                .where(StockBatch.id == stock_batch_id, StockBatch.is_active.is_(True), StockBatch.quantity_remaining + Decimal(quantity_delta) >= 0)
                .values(quantity_remaining=new_balance, updated_at=now)
            )
            if result.rowcount != 1:
                raise BusinessRuleException("Stock balance changed before the adjustment could be applied.")
            card = StockCard(
                medicine_id=batch.medicine_id,
                stock_batch_id=batch.id,
                transaction_type="Adjustment",
                quantity_in=Decimal(quantity_delta) if quantity_delta > 0 else Decimal("0"),
                quantity_out=abs(Decimal(quantity_delta)) if quantity_delta < 0 else Decimal("0"),
                balance_quantity=new_balance,
                reference_type=reference_type,
                reference_id=reference_id,
                transaction_datetime=now,
                created_by=created_by,
                remarks=remarks,
                created_at=now,
            )
            db.add(card)
            await db.commit()
            await db.refresh(card)
            return card
        except BusinessRuleException:
            await db.rollback()
            raise
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to record stock adjustment.") from exc


stock_card_service = StockCardService()
__all__ = ["StockCardService", "stock_card_service"]
