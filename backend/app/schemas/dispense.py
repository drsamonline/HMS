"""
HHMS Dispensing Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class DispenseCreate(BaseSchema):
    prescription_item_id: int = Field(gt=0)
    medicine_id: int = Field(gt=0)
    stock_batch_id: int = Field(gt=0)
    quantity_dispensed: Decimal = Field(gt=0)
    dispensed_by: int = Field(gt=0)
    notes: str | None = None


class DispenseRead(BaseSchema):
    id: int
    prescription_item_id: int
    medicine_id: int
    stock_batch_id: int
    quantity_dispensed: Decimal
    dispense_date: datetime
    dispensed_by: int
    notes: str | None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "DispenseCreate",
    "DispenseRead",
]