"""HHMS Stock Transaction Service."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.core.exceptions import BusinessRuleException, DatabaseException, ResourceNotFoundException
from app.models.inventory_item import InventoryItem
from app.models.stock_transaction import StockTransaction
from app.repositories.stock_transaction import StockTransactionRepository, stock_transaction_repository
from app.schemas.stock_transaction import StockTransactionCreate
class StockTransactionService:
    """Immutable stock ledger with transactional balance maintenance."""
    def __init__(self, repository: StockTransactionRepository | None = None) -> None:
        self.repository = repository or stock_transaction_repository
    async def get(self, db, transaction_id:int):
        tx=await self.repository.get_by_id(db,transaction_id)
        if tx is None: raise ResourceNotFoundException("Stock transaction not found.")
        return tx
    async def list_by_item(self, db, inventory_item_id:int, *, skip:int=0, limit:int=100):
        item=await db.get(InventoryItem,inventory_item_id)
        if item is None: raise ResourceNotFoundException("Inventory item not found.")
        return await self.repository.list_by_item(db,inventory_item_id,skip=skip,limit=limit)
    async def create(self, db, data:StockTransactionCreate, performed_by:int):
        item=await db.get(InventoryItem,data.inventory_item_id)
        if item is None: raise ResourceNotFoundException("Inventory item not found.")
        if not item.is_active: raise BusinessRuleException("Cannot create a stock transaction for an inactive inventory item.")
        if performed_by<=0: raise BusinessRuleException("Invalid performing user.")
        if data.quantity==0: raise BusinessRuleException("Transaction quantity cannot be zero.")
        qty=Decimal(data.quantity)
        if data.transaction_type in ("Receipt","Return"):
            delta=qty
        elif data.transaction_type=="Issue":
            if qty<0: raise BusinessRuleException("Issue quantity must be positive.")
            delta=-qty
        else:
            delta=qty
        new_balance=Decimal(item.quantity_on_hand or 0)+delta
        if new_balance<0: raise BusinessRuleException("Insufficient stock for this transaction.")
        now=datetime.now(timezone.utc)
        tx=StockTransaction(inventory_item_id=data.inventory_item_id,transaction_type=data.transaction_type,quantity=qty,reference_number=data.reference_number,transaction_datetime=data.transaction_datetime or now,performed_by=performed_by,remarks=data.remarks,created_at=now,updated_at=now)
        item.quantity_on_hand=new_balance
        item.updated_at=now
        try:
            db.add(tx)
            await db.commit(); await db.refresh(tx)
            return tx
        except IntegrityError as exc:
            await db.rollback(); raise DatabaseException("Unable to create stock transaction because a referenced record is invalid.") from exc
        except SQLAlchemyError as exc:
            await db.rollback(); raise DatabaseException("Unable to create stock transaction.") from exc
stock_transaction_service=StockTransactionService()
__all__=["StockTransactionService","stock_transaction_service"]
