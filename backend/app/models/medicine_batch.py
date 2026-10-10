"""
HHMS Medicine Batch ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MedicineBatch(Base):
    """
    Pharmacy inventory batch belonging to a Medicine.
    """

    __tablename__ = "MedicineBatch"

    __table_args__ = (
        UniqueConstraint(
            "medicine_id",
            "batch_number",
            name="uq_medicine_batch_medicine_batch_number",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Medicine.id",
            name="fk_medicine_batch_medicine",
        ),
        nullable=False,
        index=True,
    )

    batch_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    potency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    manufacture_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    purchase_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    selling_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    quantity_in_stock: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    minimum_stock: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    storage_location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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


__all__ = ["MedicineBatch"]