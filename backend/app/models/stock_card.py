"""HHMS Pharmacy Stock Card ORM Model."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class StockCard(Base):
    """Immutable ledger entry for pharmacy StockBatch movement."""
    __tablename__ = "StockCard"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("Medicine.id", name="fk_stock_card_medicine"), nullable=False, index=True)
    stock_batch_id: Mapped[int] = mapped_column(ForeignKey("StockBatch.id", name="fk_stock_card_stock_batch"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    quantity_in: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False, default=0)
    quantity_out: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False, default=0)
    balance_quantity: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    transaction_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("User.id", name="fk_stock_card_user"), nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_year: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    storage_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="live", index=True)
    is_current_year: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

__all__=["StockCard"]
