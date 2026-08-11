"""
HHMS PrescriptionItem ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PrescriptionItem(Base):
    """Individual medicine line within a prescription."""

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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


__all__ = [
    "PrescriptionItem",
]