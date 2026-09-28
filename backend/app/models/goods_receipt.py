from __future__ import annotations
from datetime import date,datetime
from decimal import Decimal
from sqlalchemy import Boolean,Date,DateTime,ForeignKey,Integer,Numeric,String,Text
from sqlalchemy.orm import Mapped,mapped_column
from app.models.base import Base
class GoodsReceipt(Base):
 __tablename__='GoodsReceipt'
 id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
 purchase_order_id:Mapped[int]=mapped_column(ForeignKey('PurchaseOrder.id',name='fk_goods_receipt_order'),nullable=False,index=True)
 receipt_no:Mapped[str]=mapped_column(String(40),nullable=False,unique=True,index=True); receipt_date:Mapped[date]=mapped_column(Date,nullable=False,index=True)
 supplier_id:Mapped[int]=mapped_column(ForeignKey('Supplier.id',name='fk_goods_receipt_supplier'),nullable=False,index=True)
 total_quantity:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False,default=0,server_default='0'); accepted_quantity:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False,default=0,server_default='0'); rejected_quantity:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False,default=0,server_default='0')
 remarks:Mapped[str|None]=mapped_column(Text); received_by:Mapped[int]=mapped_column(ForeignKey('User.id',name='fk_goods_receipt_received_by'),nullable=False)
 receipt_year:Mapped[int]=mapped_column(Integer,nullable=False,default=0,index=True)
 storage_tier:Mapped[str]=mapped_column(String(20),nullable=False,default='live',index=True)
 is_current_year:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,index=True)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
class GoodsReceiptItem(Base):
 __tablename__='GoodsReceiptItem'
 id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
 goods_receipt_id:Mapped[int]=mapped_column(ForeignKey('GoodsReceipt.id',name='fk_goods_receipt_item_receipt',ondelete='CASCADE'),nullable=False,index=True)
 purchase_order_item_id:Mapped[int]=mapped_column(ForeignKey('PurchaseOrderItem.id',name='fk_goods_receipt_item_po_item'),nullable=False,index=True)
 medicine_id:Mapped[int]=mapped_column(ForeignKey('Medicine.id',name='fk_goods_receipt_item_medicine'),nullable=False,index=True)
 batch_number:Mapped[str]=mapped_column(String(50),nullable=False); potency:Mapped[str]=mapped_column(String(20),nullable=False)
 manufacture_date:Mapped[date|None]=mapped_column(Date); expiry_date:Mapped[date|None]=mapped_column(Date)
 quantity_received:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False); unit_cost:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False); total_cost:Mapped[Decimal]=mapped_column(Numeric(14,2),nullable=False)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
__all__=['GoodsReceipt','GoodsReceiptItem']
