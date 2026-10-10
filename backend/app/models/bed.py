"""
HHMS Bed ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Bed(Base):
    """
    Master record for an inpatient hospital bed.
    """

    __tablename__ = "Bed"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    bed_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    ward: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    room_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    bed_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    occupancy_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


__all__ = [
    "Bed",
]