"""HHMS Inventory Item Schemas."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from pydantic import Field
from app.schemas.base import BaseSchema
class InventoryItemCreate(BaseSchema):
    item_code: str = Field(min_length=1,max_length=30)
    item_name: str = Field(min_length=1,max_length=150)
    category: str | None = Field(default=None,max_length=100)
    unit: str | None = Field(default=None,max_length=30)
    description: str | None = None
class InventoryItemUpdate(BaseSchema):
    item_name: str | None = Field(default=None,min_length=1,max_length=150)
    category: str | None = Field(default=None,max_length=100)
    unit: str | None = Field(default=None,max_length=30)
    description: str | None = None
    is_active: bool | None = None
class InventoryItemRead(BaseSchema):
    id: int
    item_code: str
    item_name: str
    category: str | None
    unit: str | None
    description: str | None
    quantity_on_hand: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
__all__=["InventoryItemCreate","InventoryItemUpdate","InventoryItemRead"]
