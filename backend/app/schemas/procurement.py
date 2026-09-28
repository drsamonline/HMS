from __future__ import annotations
from datetime import date,datetime
from decimal import Decimal
from pydantic import Field
from app.schemas.base import BaseSchema
class SupplierCreate(BaseSchema):
 supplier_name:str=Field(min_length=1,max_length=150); contact_person:str|None=None; mobile:str|None=None; email:str|None=None; address:str|None=None; city:str|None=None; state:str|None=None; pincode:str|None=None; gst_no:str|None=None; drug_license_no:str|None=None
class SupplierRead(SupplierCreate): id:int; is_active:bool; created_at:datetime; updated_at:datetime
class PurchaseOrderItemCreate(BaseSchema): medicine_id:int=Field(gt=0); quantity_ordered:Decimal=Field(gt=0); unit_cost:Decimal=Field(ge=0)
class PurchaseOrderCreate(BaseSchema): supplier_id:int=Field(gt=0); order_date:date; expected_delivery_date:date|None=None; notes:str|None=None; items:list[PurchaseOrderItemCreate]=Field(min_length=1)
class PurchaseOrderItemRead(BaseSchema): id:int; purchase_order_id:int; medicine_id:int; quantity_ordered:Decimal; unit_cost:Decimal; total_cost:Decimal; quantity_received:Decimal; created_at:datetime; updated_at:datetime
class PurchaseOrderRead(BaseSchema): id:int; order_no:str; supplier_id:int; order_date:date; expected_delivery_date:date|None; status:str; total_amount:Decimal; notes:str|None; created_by:int; order_year:int; storage_tier:str; is_current_year:bool; created_at:datetime; updated_at:datetime; items:list[PurchaseOrderItemRead]
class GoodsReceiptItemCreate(BaseSchema): purchase_order_item_id:int=Field(gt=0); batch_number:str=Field(min_length=1,max_length=50); potency:str=Field(min_length=1,max_length=20); manufacture_date:date|None=None; expiry_date:date|None=None; quantity_received:Decimal=Field(gt=0); unit_cost:Decimal=Field(ge=0)
class GoodsReceiptCreate(BaseSchema): purchase_order_id:int=Field(gt=0); receipt_date:date; remarks:str|None=None; items:list[GoodsReceiptItemCreate]=Field(min_length=1)
class GoodsReceiptRead(BaseSchema): id:int; purchase_order_id:int; receipt_no:str; receipt_date:date; supplier_id:int; total_quantity:Decimal; accepted_quantity:Decimal; rejected_quantity:Decimal; remarks:str|None; received_by:int; receipt_year:int; storage_tier:str; is_current_year:bool; created_at:datetime; updated_at:datetime
