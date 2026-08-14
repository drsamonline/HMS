from __future__ import annotations
from datetime import datetime,timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from app.core.exceptions import BusinessRuleException,DatabaseException,DuplicateResourceException,ResourceNotFoundException
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder,PurchaseOrderItem
from app.models.goods_receipt import GoodsReceipt,GoodsReceiptItem
from app.models.medicine import Medicine
from app.models.medicine_batch import MedicineBatch
from app.schemas.procurement import SupplierCreate,PurchaseOrderCreate,GoodsReceiptCreate
class ProcurementService:
 async def list_suppliers(self,db:AsyncSession): return list((await db.execute(select(Supplier).where(Supplier.is_active.is_(True)).order_by(Supplier.supplier_name))).scalars().all())
 async def create_supplier(self,db:AsyncSession,data:SupplierCreate):
  existing=await db.scalar(select(Supplier).where(Supplier.supplier_name==data.supplier_name.strip()))
  if existing: raise DuplicateResourceException('Supplier already exists.')
  now=datetime.now(timezone.utc); row=Supplier(**data.model_dump(),is_active=True,created_at=now,updated_at=now); db.add(row)
  try: await db.commit(); await db.refresh(row); return row
  except IntegrityError as exc: await db.rollback(); raise DuplicateResourceException('Unable to create supplier.') from exc
  except SQLAlchemyError as exc: await db.rollback(); raise DatabaseException('Unable to create supplier.') from exc
 async def list_purchase_orders(self,db:AsyncSession,status:str|None=None):
  stmt=select(PurchaseOrder).order_by(PurchaseOrder.order_date.desc(),PurchaseOrder.id.desc())
  if status: stmt=stmt.where(PurchaseOrder.status==status)
  return list((await db.execute(stmt)).scalars().all())
 async def create_purchase_order(self,db:AsyncSession,data:PurchaseOrderCreate,created_by:int):
  if await db.get(Supplier,data.supplier_id) is None: raise ResourceNotFoundException('Supplier not found.')
  now=datetime.now(timezone.utc); order=PurchaseOrder(order_no=f"PO-{now.strftime('%Y%m%d%H%M%S%f')[:-3]}",supplier_id=data.supplier_id,order_date=data.order_date,expected_delivery_date=data.expected_delivery_date,status='Ordered',total_amount=0,notes=data.notes,created_by=created_by,created_at=now,updated_at=now); db.add(order); await db.flush(); total=Decimal('0')
  for item in data.items:
   if await db.get(Medicine,item.medicine_id) is None: raise ResourceNotFoundException(f'Medicine {item.medicine_id} not found.')
   line=item.quantity_ordered*item.unit_cost; total+=line; db.add(PurchaseOrderItem(purchase_order_id=order.id,medicine_id=item.medicine_id,quantity_ordered=item.quantity_ordered,unit_cost=item.unit_cost,total_cost=line,quantity_received=0,created_at=now,updated_at=now))
  order.total_amount=total
  try: await db.commit(); await db.refresh(order); return order
  except SQLAlchemyError as exc: await db.rollback(); raise DatabaseException('Unable to create purchase order.') from exc
 async def receive_goods(self,db:AsyncSession,data:GoodsReceiptCreate,received_by:int):
  order=await db.get(PurchaseOrder,data.purchase_order_id)
  if order is None: raise ResourceNotFoundException('Purchase order not found.')
  po_items={i.id:i for i in (await db.execute(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id))).scalars().all()}; now=datetime.now(timezone.utc)
  receipt=GoodsReceipt(purchase_order_id=order.id,receipt_no=f"GRN-{now.strftime('%Y%m%d%H%M%S%f')[:-3]}",receipt_date=data.receipt_date,supplier_id=order.supplier_id,total_quantity=0,accepted_quantity=0,rejected_quantity=0,remarks=data.remarks,received_by=received_by,created_at=now,updated_at=now); db.add(receipt); await db.flush(); total=Decimal('0')
  for incoming in data.items:
   po=po_items.get(incoming.purchase_order_item_id)
   if po is None: raise ResourceNotFoundException('Purchase order item not found.')
   if incoming.quantity_received > po.quantity_ordered-po.quantity_received: raise BusinessRuleException(f'Received quantity exceeds remaining ordered quantity for item {po.id}.')
   medicine=await db.get(Medicine,po.medicine_id)
   if medicine is None: raise ResourceNotFoundException('Medicine not found for purchase order item.')
   total+=incoming.quantity_received; po.quantity_received+=incoming.quantity_received; po.updated_at=now
   db.add(GoodsReceiptItem(goods_receipt_id=receipt.id,purchase_order_item_id=po.id,medicine_id=medicine.id,batch_number=incoming.batch_number,potency=incoming.potency,manufacture_date=incoming.manufacture_date,expiry_date=incoming.expiry_date,quantity_received=incoming.quantity_received,unit_cost=incoming.unit_cost,total_cost=incoming.quantity_received*incoming.unit_cost,created_at=now,updated_at=now))
   db.add(MedicineBatch(medicine_id=medicine.id,batch_number=incoming.batch_number,potency=incoming.potency,manufacture_date=incoming.manufacture_date,expiry_date=incoming.expiry_date,purchase_price=incoming.unit_cost,selling_price=incoming.unit_cost,quantity_in_stock=incoming.quantity_received,minimum_stock=None,storage_location=None,is_active=True,created_at=now,updated_at=now))
  receipt.total_quantity=total; receipt.accepted_quantity=total; all_items=list((await db.execute(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id==order.id))).scalars().all()); order.status='Received' if all(i.quantity_received>=i.quantity_ordered for i in all_items) else 'Partially Received'; order.updated_at=now
  try: await db.commit(); await db.refresh(receipt); return receipt
  except IntegrityError as exc: await db.rollback(); raise DuplicateResourceException('Unable to complete goods receipt; batch or reference may already exist.') from exc
  except SQLAlchemyError as exc: await db.rollback(); raise DatabaseException('Unable to complete goods receipt.') from exc
procurement_service=ProcurementService()
