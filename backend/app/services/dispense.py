"""HHMS transactional pharmacy dispensing service."""
from __future__ import annotations
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BusinessRuleException, DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.dispense_record import DispenseRecord
from app.models.prescription_item import PrescriptionItem
from app.models.stock_batch import StockBatch
from app.repositories.dispense import DispenseRepository, dispense_repository
from app.schemas.dispense import DispenseCreate
from app.services.operational_year import operational_year_service
from app.services.stock_card import stock_card_service


class DispenseService:
    """Create a dispense record and matching stock-card issue atomically."""
    def __init__(self, repository: DispenseRepository | None = None) -> None:
        self.repository = repository or dispense_repository

    async def get(self, db: AsyncSession, dispense_id: int) -> DispenseRecord:
        record = await self.repository.get_by_id(db, dispense_id)
        if record is None:
            raise ResourceNotFoundException("Dispense record not found.")
        return record

    async def list_by_prescription_item(self, db: AsyncSession, prescription_item_id: int) -> list[DispenseRecord]:
        return await self.repository.list_by_prescription_item(db, prescription_item_id)

    async def create(self, db: AsyncSession, data: DispenseCreate, performed_by: int) -> DispenseRecord:
        if performed_by <= 0:
            raise BusinessRuleException("Authenticated dispensing user is invalid.")
        prescription_item = await db.get(PrescriptionItem, data.prescription_item_id)
        if prescription_item is None:
            raise ResourceNotFoundException("Prescription item not found.")
        if prescription_item.medicine_id != data.medicine_id:
            raise BusinessRuleException("Dispensing medicine does not match the prescribed medicine.")

        stock_batch = await db.get(StockBatch, data.stock_batch_id)
        if stock_batch is None:
            raise ResourceNotFoundException("Stock batch not found.")
        if stock_batch.medicine_id != data.medicine_id:
            raise BusinessRuleException("Selected stock batch does not belong to the prescribed medicine.")
        if not stock_batch.is_active:
            raise BusinessRuleException("Selected stock batch is inactive.")
        if stock_batch.expiry_date is not None and stock_batch.expiry_date < date.today():
            raise BusinessRuleException("Expired stock cannot be dispensed.")

        already_dispensed = await db.scalar(
            select(func.coalesce(func.sum(DispenseRecord.quantity_dispensed), 0)).where(
                DispenseRecord.prescription_item_id == data.prescription_item_id
            )
        )
        requested = Decimal(data.quantity_dispensed)
        remaining_prescription = Decimal(prescription_item.quantity) - Decimal(already_dispensed or 0)
        if requested <= 0:
            raise BusinessRuleException("Dispense quantity must be greater than zero.")
        if requested > remaining_prescription:
            raise BusinessRuleException("Dispense quantity exceeds the remaining prescribed quantity.")

        now = datetime.now(timezone.utc)
        try:
            result = await db.execute(
                update(StockBatch)
                .where(
                    StockBatch.id == data.stock_batch_id,
                    StockBatch.medicine_id == data.medicine_id,
                    StockBatch.is_active.is_(True),
                    StockBatch.quantity_remaining >= requested,
                )
                .values(
                    quantity_remaining=StockBatch.quantity_remaining - requested,
                    updated_at=now,
                )
            )
            if result.rowcount != 1:
                raise BusinessRuleException("Insufficient stock in the selected batch.")

            await db.refresh(stock_batch)

            # Derive the annual lifecycle fields from the dispense date so every
            # dispense record carries its operational-year identity at creation.
            dispense_local_date = (
                now.astimezone(timezone.utc).date()
                if now.tzinfo is not None
                else now.date()
            )
            op_cfg = await operational_year_service.get_config(db)
            dispense_year = operational_year_service.current_year(dispense_local_date, op_cfg)
            current_year = operational_year_service.current_year(date.today(), op_cfg)

            record = DispenseRecord(
                prescription_item_id=data.prescription_item_id,
                medicine_id=data.medicine_id,
                stock_batch_id=data.stock_batch_id,
                quantity_dispensed=requested,
                dispense_date=now,
                dispensed_by=performed_by,
                dispense_year=dispense_year,
                storage_tier="live",
                is_current_year=dispense_year == current_year,
                notes=data.notes,
                created_at=now,
                updated_at=now,
            )
            db.add(record)
            await stock_card_service.record(
                db,
                batch=stock_batch,
                transaction_type="DISPENSE",
                quantity_in=Decimal("0"),
                quantity_out=requested,
                performed_by=performed_by,
                reference_type="DISPENSE",
                remarks=f"Dispense against prescription item {data.prescription_item_id}",
            )
            await db.commit()
            await db.refresh(record)
            return record
        except BusinessRuleException:
            await db.rollback()
            raise
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateResourceException("Dispensing failed because a referenced record is invalid.") from exc
        except SQLAlchemyError as exc:
            await db.rollback()
            raise DatabaseException("Unable to create dispense record and update pharmacy stock ledger.") from exc


dispense_service = DispenseService()
__all__ = ["DispenseService", "dispense_service"]
