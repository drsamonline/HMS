"""
HHMS Inventory Item Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class InventoryItemCreate(BaseSchema):
    medicine_id: int = Field(gt=0)
    current_quantity: Decimal = Field(ge=0)
    minimum_quantity: Decimal = Field(ge=0)
    maximum_quantity: Decimal | None = Field(
        default=None,
        ge=0,
    )
    storage_location: str | None = Field(
        default=None,
        max_length=100,
    )


class InventoryItemUpdate(BaseSchema):
    minimum_quantity: Decimal | None = Field(
        default=None,
        ge=0,
    )
    maximum_quantity: Decimal | None = Field(
        default=None,
        ge=0,
    )
    storage_location: str | None = Field(
        default=None,
        max_length=100,
    )
    is_active: bool | None = None


class InventoryItemRead(BaseSchema):
    id: int
    medicine_id: int
    current_quantity: Decimal
    minimum_quantity: Decimal
    maximum_quantity: Decimal | None
    storage_location: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


__all__ = [
    "InventoryItemCreate",
    "InventoryItemUpdate",
    "InventoryItemRead",
]