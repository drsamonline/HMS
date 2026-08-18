from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BusinessRuleException, DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.goods_receipt import GoodsReceipt, GoodsReceiptItem
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.stock_batch import StockBatch
from app.repositories.goods_receipt import goods_receipt_repository
from app.schemas.goods_receipt import GoodsReceiptCreate
from app.services.stock_card import stock_card_service

class GoodsReceiptService:
    async def get(self, db: AsyncSession, receipt_id: int) -> GoodsReceipt:
        receipt = await goods_receipt_repository.get_by_id(db, receipt_id)
        if receipt is None:
            raise ResourceNotFoundException("Goods receipt not found.")
        return receipt

    async def list_items(self, db: AsyncSession, receipt_id: int) -> list[GoodsReceiptItem]:
        await self.get(db, receipt_id)
        return await goods_receipt_repository.list_items(db, receipt_id)

    async def create(self, db: AsyncSession, data: GoodsReceiptCreate, received_by: int) -> GoodsReceipt:
        if received_by <= 0:
            raise BusinessRuleException("Authenticated receiving user is invalid.")
        order = await db.get(PurchaseOrder, data.purchase_order_id)
        if order is None:
            raise ResourceNotFoundException("Purchase order not found.")
        if order.supplier_id != data.supplier_id:
            raise BusinessRuleException("Goods receipt supplier does not match the purchase order supplier.")
        if await goods_receipt_repository.get_by_receipt_no(db, data.receipt_no):
            raise DuplicateResourceException("Goods receipt number already exists.")
        now = datetime.now(timezone.utc)
        receipt = GoodsReceipt(
            purchase_order_id=order.id, receipt_no=data.receipt_no, receipt_date=data.receipt_date,
            supplier_id=data.supplier_id,
            total_quantity=sum((Decimal(i.quantity_received) for i in data.items), Decimal("0")),
            accepted_quantity=sum((Decimal(i.quantity_received) for i in data.items), Decimal("0")),
            rejected_quantity=Decimal("0"), remarks=data.remarks, received_by=received_by,
            created_at=now, updated_at=now,
        )
        db.add(receipt)
        await db.flush()
        try:
            seen_po_items: set[int] = set()
            for item in data.items:
                if item.purchase_order_item_id in seen_po_items:
                    raise BusinessRuleException("A purchase-order line cannot occur more than once in a receipt.")
                seen_po_items.add(item.purchase_order_item_id)
                po_item = await db.get(PurchaseOrderItem, item.purchase_order_item_id)
                if po_item is None or po_item.purchase_order_id != order.id:
                    raise BusinessRuleException("A goods-receipt item does not belong to the selected purchase order.")
                if item.medicine_id != po_item.medicine_id:
                    raise BusinessRuleException(f"Medicine mismatch for purchase-order item {po_item.id}.")
                outstanding = Decimal(po_item.quantity_ordered) - Decimal(po_item.quantity_received or 0)
                if Decimal(item.quantity_received) > outstanding:
                    raise BusinessRuleException(f"Receipt quantity exceeds outstanding purchase-order quantity for item {po_item.id}.")
                db.add(GoodsReceiptItem(
                    goods_receipt_id=receipt.id, purchase_order_item_id=po_item.id,
                    medicine_id=item.medicine_id, batch_number=item.batch_number, potency=item.potency,
                    manufacture_date=item.manufacture_date, expiry_date=item.expiry_date,
                    quantity_received=item.quantity_received, unit_cost=item.unit_cost,
                    total_cost=Decimal(item.quantity_received) * Decimal(item.unit_cost),
                    created_at=now, updated_at=now,
                ))
                po_item.quantity_received = Decimal(po_item.quantity_received or 0) + Decimal(item.quantity_received)
                po_item.updated_at = now
                batch = StockBatch(
                    medicine_id=item.medicine_id, batch_no=item.batch_number,
                    expiry_date=item.expiry_date, manufacture_date=item.manufacture_date,
                    quantity_received=item.quantity_received, quantity_remaining=item.quantity_received,
                    unit_cost=item.unit_cost, total_cost=Decimal(item.quantity_received) * Decimal(item.unit_cost),
                    supplier_id=data.supplier_id, goods_receipt_id=receipt.id, is_active=True,
                    created_at=now, updated_at=now,
                )
                db.add(batch)
                await db.flush()
                await stock_card_service.record(
                    db, batch=batch, transaction_type="RECEIPT",
                    quantity_in=Decimal(item.quantity_received), quantity_out=Decimal("0"),
                    performed_by=received_by, reference_type="GOODS_RECEIPT",
                    reference_id=receipt.id, remarks=f"Receipt {data.receipt_no}",
                )
            result = await db.execute(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == order.id))
            order.status = "Received" if all(Decimal(line.quantity_received or 0) >= Decimal(line.quantity_ordered) for line in result.scalars().all()) else "PartiallyReceived"
            order.updated_at = now
            await db.commit()
            await db.refresh(receipt)
            return receipt
        except (BusinessRuleException, DuplicateResourceException):
            await db.rollback(); raise
        except IntegrityError as exc:
            await db.rollback(); raise DatabaseException("Unable to post goods receipt because a referenced record is invalid.") from exc
        except SQLAlchemyError as exc:
            await db.rollback(); raise DatabaseException("Unable to post goods receipt.") from exc

goods_receipt_service = GoodsReceiptService()
