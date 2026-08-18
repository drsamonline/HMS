"""Schemas for the pharmacy batch stock ledger."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import Field
from app.schemas.base import BaseSchema

StockCardTransactionType = Literal["Receipt", "Issue", "Adjustment", "Return"]


class StockCardCreate(BaseSchema):
    transaction_type: StockCardTransactionType
    quantity: Decimal = Field(gt=0)
    reference_type: str | None = Field(default=None, max_length=40)
    reference_id: int | None = Field(default=None, gt=0)
    transaction_datetime: datetime | None = None
    remarks: str | None = None


class StockCardRead(BaseSchema):
    id: int
    medicine_id: int
    stock_batch_id: int
    transaction_type: StockCardTransactionType
    quantity_in: Decimal
    quantity_out: Decimal
    balance_quantity: Decimal
    reference_type: str | None
    reference_id: int | None
    transaction_datetime: datetime
    created_by: int
    remarks: str | None
    created_at: datetime


__all__ = ["StockCardTransactionType", "StockCardCreate", "StockCardRead"]
