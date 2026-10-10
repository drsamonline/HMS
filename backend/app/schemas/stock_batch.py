"""
HHMS Stock Batch Schemas.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class StockBatchCreate(BaseSchema):
    medicine_id: int = Field(gt=0)
    batch_no: str = Field(
        min_length=1,
        max_length=50,
    )
    expiry_date: date | None = None
    manufacture_date: date | None = None
    quantity_received: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    supplier_id: int | None = Field(
        default=None,
        gt=0,
    )
    goods_receipt_id: int | None = Field(
        default=None,
        gt=0,
    )


class StockBatchUpdate(BaseSchema):
    expiry_date: date | None = None
    manufacture_date: date | None = None
    is_active: bool | None = None


class StockBatchRead(BaseSchema):
    id: int
    medicine_id: int
    batch_no: str
    expiry_date: date | None
    manufacture_date: date | None
    quantity_received: Decimal
    quantity_remaining: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    supplier_id: int | None
    goods_receipt_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


__all__ = [
    "StockBatchCreate",
    "StockBatchUpdate",
    "StockBatchRead",
]