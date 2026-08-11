"""
HHMS Stock Transaction Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class StockTransactionCreate(BaseSchema):
    inventory_item_id: int = Field(gt=0)
    transaction_type: str = Field(
        min_length=1,
        max_length=30,
    )
    quantity: Decimal = Field(gt=0)
    reference_number: str | None = Field(
        default=None,
        max_length=50,
    )
    performed_by: int = Field(gt=0)
    remarks: str | None = None


class StockTransactionRead(BaseSchema):
    id: int
    inventory_item_id: int
    transaction_type: str
    quantity: Decimal
    reference_number: str | None
    transaction_datetime: datetime
    performed_by: int
    remarks: str | None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "StockTransactionCreate",
    "StockTransactionRead",
]