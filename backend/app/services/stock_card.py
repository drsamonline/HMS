"""HHMS Pharmacy Stock Card Service."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BusinessRuleException, DatabaseException, ResourceNotFoundException
from app.models.stock_batch import StockBatch
from app.models.stock_card import StockCard
from app.repositories.stock_card import stock_card_repository
from app.schemas.stock_card import StockAdjustmentCreate

class StockCardService:
    async def list_by_batch(self,db:AsyncSession,stock_batch_id:int,skip:int=0,limit:int=200):
        return await stock_card_repository.list_by_batch(db,stock_batch_id,skip,limit)
    async def list_by_medicine(self,db:AsyncSession,medicine_id:int,skip:int=0,limit:int=200):
        return await stock_card_repository.list_by_medicine(db,medicine_id,skip,limit)
    async def record(self,db:AsyncSession,*,batch:StockBatch,transaction_type:str,quantity_in:Decimal,quantity_out:Decimal,performed_by:int,reference_type:str|None=None,reference_id:int|None=None,remarks:str|None=None,commit:bool=False)->StockCard:
        now=datetime.now(timezone.utc)
        card=StockCard(medicine_id=batch.medicine_id,stock_batch_id=batch.id,transaction_type=transaction_type,quantity_in=quantity_in,quantity_out=quantity_out,balance_quantity=Decimal(batch.quantity_remaining),reference_type=reference_type,reference_id=reference_id,transaction_datetime=now,created_by=performed_by,remarks=remarks,created_at=now)
        db.add(card)
        if commit:
            try:
                await db.commit(); await db.refresh(card)
            except SQLAlchemyError as exc:
                await db.rollback(); raise DatabaseException("Unable to record stock card entry.") from exc
        else:
            await db.flush()
        return card
    async def adjust(self,db:AsyncSession,data:StockAdjustmentCreate,performed_by:int)->StockBatch:
        if performed_by<=0: raise BusinessRuleException("Authenticated stock operator is invalid.")
        batch=await db.get(StockBatch,data.stock_batch_id)
        if batch is None: raise ResourceNotFoundException("Stock batch not found.")
        if not batch.is_active: raise BusinessRuleException("Cannot adjust inactive stock batch.")
        qty=Decimal(data.quantity); current=Decimal(batch.quantity_remaining)
        if data.adjustment_type=="OUT" and qty>current: raise BusinessRuleException("Stock adjustment cannot reduce stock below zero.")
        batch.quantity_remaining = current + qty if data.adjustment_type=="IN" else current - qty
        batch.updated_at=datetime.now(timezone.utc)
        await self.record(db,batch=batch,transaction_type="ADJUSTMENT_IN" if data.adjustment_type=="IN" else "ADJUSTMENT_OUT",quantity_in=qty if data.adjustment_type=="IN" else Decimal("0"),quantity_out=qty if data.adjustment_type=="OUT" else Decimal("0"),performed_by=performed_by,reference_type="STOCK_ADJUSTMENT",remarks=data.reason if not data.remarks else f"{data.reason} — {data.remarks}")
        try:
            await db.commit(); await db.refresh(batch); return batch
        except SQLAlchemyError as exc:
            await db.rollback(); raise DatabaseException("Unable to apply stock adjustment.") from exc
stock_card_service=StockCardService()
__all__=["StockCardService","stock_card_service"]
