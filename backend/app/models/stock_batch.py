"""
HHMS Stock Batch ORM Model.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StockBatch(Base):
    """Medicine stock maintained batch-wise."""

    __tablename__ = "StockBatch"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Medicine.id",
            name="fk_stock_batch_medicine",
        ),
        nullable=False,
        index=True,
    )

    batch_no: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    manufacture_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    quantity_remaining: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "Supplier.id",
            name="fk_stock_batch_supplier",
        ),
        nullable=True,
        index=True,
    )

    goods_receipt_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "GoodsReceipt.id",
            name="fk_stock_batch_goods_receipt",
        ),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


__all__ = ["StockBatch"]