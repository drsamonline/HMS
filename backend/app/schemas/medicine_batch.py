"""
HHMS Medicine Batch Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class MedicineBatchCreate(BaseSchema):
    medicine_id: int = Field(gt=0)
    batch_number: str = Field(
        min_length=1,
        max_length=50,
    )
    potency: str = Field(
        min_length=1,
        max_length=20,
    )
    manufacturer: str | None = Field(
        default=None,
        max_length=150,
    )
    manufacture_date: date | None = None
    expiry_date: date | None = None
    purchase_price: Decimal | None = Field(
        default=None,
        ge=0,
    )
    selling_price: Decimal | None = Field(
        default=None,
        ge=0,
    )
    quantity_in_stock: Decimal = Field(
        ge=0,
    )
    minimum_stock: Decimal | None = Field(
        default=None,
        ge=0,
    )
    storage_location: str | None = Field(
        default=None,
        max_length=100,
    )


class MedicineBatchUpdate(BaseSchema):
    manufacturer: str | None = Field(
        default=None,
        max_length=150,
    )
    manufacture_date: date | None = None
    expiry_date: date | None = None
    purchase_price: Decimal | None = Field(
        default=None,
        ge=0,
    )
    selling_price: Decimal | None = Field(
        default=None,
        ge=0,
    )
    quantity_in_stock: Decimal | None = Field(
        default=None,
        ge=0,
    )
    minimum_stock: Decimal | None = Field(
        default=None,
        ge=0,
    )
    storage_location: str | None = Field(
        default=None,
        max_length=100,
    )
    is_active: bool | None = None


class MedicineBatchRead(BaseSchema):
    id: int
    medicine_id: int
    batch_number: str
    potency: str
    manufacturer: str | None
    manufacture_date: date | None
    expiry_date: date | None
    purchase_price: Decimal | None
    selling_price: Decimal | None
    quantity_in_stock: Decimal
    minimum_stock: Decimal | None
    storage_location: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


__all__ = [
    "MedicineBatchCreate",
    "MedicineBatchUpdate",
    "MedicineBatchRead",
]