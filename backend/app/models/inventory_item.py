"""HHMS Inventory Item ORM Model."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class InventoryItem(Base):
    """General non-pharmacy inventory item with current stock balance."""
    __tablename__ = "InventoryItem"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    item_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
__all__=["InventoryItem"]
