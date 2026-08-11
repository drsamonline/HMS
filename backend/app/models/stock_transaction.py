"""
HHMS StockTransaction ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StockTransaction(Base):
    """
    Records movement of a general inventory item.
    """

    __tablename__ = "StockTransaction"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    inventory_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "InventoryItem.id",
            name="fk_stock_transaction_inventory_item",
        ),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    reference_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    transaction_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    performed_by: Mapped[int] = mapped_column(
        ForeignKey(
            "User.id",
            name="fk_stock_transaction_user",
        ),
        nullable=False,
        index=True,
    )

    remarks: Mapped[str | None] = mapped_column(
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


__all__ = [
    "StockTransaction",
]