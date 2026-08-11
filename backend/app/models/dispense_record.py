"""
HHMS Dispense Record ORM Model.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DispenseRecord(Base):
    """Records medicine dispensed against a prescription item."""

    __tablename__ = "DispenseRecord"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    prescription_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "PrescriptionItem.id",
            name="fk_dispense_prescription_item",
        ),
        nullable=False,
        index=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Medicine.id",
            name="fk_dispense_medicine",
        ),
        nullable=False,
        index=True,
    )

    stock_batch_id: Mapped[int] = mapped_column(
        ForeignKey(
            "StockBatch.id",
            name="fk_dispense_stock_batch",
        ),
        nullable=False,
        index=True,
    )

    quantity_dispensed: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    dispense_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    dispensed_by: Mapped[int] = mapped_column(
        ForeignKey(
            "User.id",
            name="fk_dispense_user",
        ),
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


__all__ = ["DispenseRecord"]