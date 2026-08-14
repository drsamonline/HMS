from __future__ import annotations
from datetime import date,datetime
from decimal import Decimal
from sqlalchemy import Date,DateTime,ForeignKey,Numeric,String,Text
from sqlalchemy.orm import Mapped,mapped_column
from app.models.base import Base
class PurchaseOrder(Base):
 __tablename__='PurchaseOrder'
 id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
 order_no:Mapped[str]=mapped_column(String(40),nullable=False,unique=True,index=True)
 supplier_id:Mapped[int]=mapped_column(ForeignKey('Supplier.id',name='fk_purchase_order_supplier'),nullable=False,index=True)
 order_date:Mapped[date]=mapped_column(Date,nullable=False,index=True); expected_delivery_date:Mapped[date|None]=mapped_column(Date)
 status:Mapped[str]=mapped_column(String(20),nullable=False,default='Draft',server_default='Draft',index=True)
 total_amount:Mapped[Decimal]=mapped_column(Numeric(14,2),nullable=False,default=0,server_default='0')
 notes:Mapped[str|None]=mapped_column(Text); created_by:Mapped[int]=mapped_column(ForeignKey('User.id',name='fk_purchase_order_created_by'),nullable=False)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
class PurchaseOrderItem(Base):
 __tablename__='PurchaseOrderItem'
 id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
 purchase_order_id:Mapped[int]=mapped_column(ForeignKey('PurchaseOrder.id',name='fk_purchase_order_item_order',ondelete='CASCADE'),nullable=False,index=True)
 medicine_id:Mapped[int]=mapped_column(ForeignKey('Medicine.id',name='fk_purchase_order_item_medicine'),nullable=False,index=True)
 quantity_ordered:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False); unit_cost:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False); total_cost:Mapped[Decimal]=mapped_column(Numeric(14,2),nullable=False)
 quantity_received:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False,default=0,server_default='0')
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
__all__=['PurchaseOrder','PurchaseOrderItem']
