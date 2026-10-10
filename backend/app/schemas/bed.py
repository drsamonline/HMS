"""
HHMS Bed Schemas.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


BedOccupancyStatus = Literal[
    "available",
    "occupied",
    "maintenance",
    "blocked",
]


class BedCreate(BaseSchema):
    bed_number: str = Field(
        min_length=1,
        max_length=20,
    )
    ward: str | None = Field(
        default=None,
        max_length=100,
    )
    room_number: str | None = Field(
        default=None,
        max_length=50,
    )
    bed_type: str | None = Field(
        default=None,
        max_length=50,
    )
    occupancy_status: BedOccupancyStatus = "available"


class BedUpdate(BaseSchema):
    ward: str | None = Field(
        default=None,
        max_length=100,
    )
    room_number: str | None = Field(
        default=None,
        max_length=50,
    )
    bed_type: str | None = Field(
        default=None,
        max_length=50,
    )
    occupancy_status: BedOccupancyStatus | None = None
    is_active: bool | None = None


class BedRead(BaseSchema):
    id: int
    bed_number: str
    ward: str | None
    room_number: str | None
    bed_type: str | None
    occupancy_status: BedOccupancyStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


__all__ = [
    "BedOccupancyStatus",
    "BedCreate",
    "BedUpdate",
    "BedRead",
]