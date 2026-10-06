"""
HHMS Medicine Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class MedicineCreate(BaseSchema):
    medicine_code: str = Field(
        min_length=1,
        max_length=30,
    )
    medicine_name: str = Field(
        min_length=1,
        max_length=150,
    )
    scientific_name: str | None = Field(
        default=None,
        max_length=200,
    )
    medicine_type: str = Field(
        min_length=1,
        max_length=30,
    )
    description: str | None = None


class MedicineUpdate(BaseSchema):
    medicine_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    scientific_name: str | None = Field(
        default=None,
        max_length=200,
    )
    medicine_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )
    description: str | None = None
    is_active: bool | None = None


class MedicineRead(BaseSchema):
    id: int
    medicine_code: str
    medicine_name: str
    scientific_name: str | None
    medicine_type: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


__all__ = [
    "MedicineCreate",
    "MedicineUpdate",
    "MedicineRead",
]