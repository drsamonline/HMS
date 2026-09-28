"""
HHMS Stock Transaction Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


StockTransactionType = Literal[
    "Receipt",
    "Issue",
    "Adjustment",
    "Return",
]


class StockTransactionCreate(BaseSchema):
    inventory_item_id: int = Field(gt=0)

    transaction_type: StockTransactionType

    quantity: Decimal = Field(
        description=(
            "Positive quantity for Receipt, Issue and Return. "
            "Adjustment may be positive or negative."
        )
    )

    reference_number: str | None = Field(
        default=None,
        max_length=50,
    )

    transaction_datetime: datetime | None = None

    remarks: str | None = None


class StockTransactionRead(BaseSchema):
    id: int
    inventory_item_id: int
    transaction_type: StockTransactionType
    quantity: Decimal
    reference_number: str | None
    transaction_datetime: datetime
    performed_by: int
    remarks: str | None
    transaction_year: int
    storage_tier: str
    is_current_year: bool
    created_at: datetime
    updated_at: datetime


__all__ = [
    "StockTransactionType",
    "StockTransactionCreate",
    "StockTransactionRead",
]