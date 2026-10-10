"""
HHMS Prescription Item ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PrescriptionItem(Base):
    """Individual medicine prescribed within a prescription."""

    __tablename__ = "PrescriptionItem"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    prescription_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Prescription.id",
            name="fk_prescription_item_prescription",
        ),
        nullable=False,
        index=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Medicine.id",
            name="fk_prescription_item_medicine",
        ),
        nullable=False,
        index=True,
    )

    dosage: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    frequency: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    duration_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    item_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    storage_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="live",
        index=True,
    )

    is_current_year: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


__all__ = ["PrescriptionItem"]