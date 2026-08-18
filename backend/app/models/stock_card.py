"""HHMS pharmacy batch stock ledger."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class StockCard(Base):
    """Immutable movement ledger for a pharmacy StockBatch."""
    __tablename__ = "StockCard"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("Medicine.id", name="fk_stock_card_medicine"), nullable=False, index=True)
    stock_batch_id: Mapped[int] = mapped_column(ForeignKey("StockBatch.id", name="fk_stock_card_stock_batch"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    quantity_in: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    quantity_out: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    balance_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    transaction_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("User.id", name="fk_stock_card_user"), nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["StockCard"]
