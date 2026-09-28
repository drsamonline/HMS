from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from pydantic import Field
from app.schemas.base import BaseSchema

class GoodsReceiptItemCreate(BaseSchema):
    purchase_order_item_id: int = Field(gt=0)
    medicine_id: int = Field(gt=0)
    batch_number: str = Field(min_length=1, max_length=50)
    potency: str = Field(min_length=1, max_length=20)
    manufacture_date: date | None = None
    expiry_date: date | None = None
    quantity_received: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)

class GoodsReceiptCreate(BaseSchema):
    purchase_order_id: int = Field(gt=0)
    receipt_no: str = Field(min_length=1, max_length=40)
    receipt_date: date
    supplier_id: int = Field(gt=0)
    remarks: str | None = None
    items: list[GoodsReceiptItemCreate] = Field(min_length=1)

class GoodsReceiptRead(BaseSchema):
    id: int
    purchase_order_id: int
    receipt_no: str
    receipt_date: date
    supplier_id: int
    total_quantity: Decimal
    accepted_quantity: Decimal
    rejected_quantity: Decimal
    remarks: str | None
    received_by: int
    receipt_year: int
    storage_tier: str
    is_current_year: bool
    created_at: datetime
    updated_at: datetime
