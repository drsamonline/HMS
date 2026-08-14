"""HHMS number-sequence ORM model."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class NumberSequence(Base):
    __tablename__ = "NumberSequence"
    __table_args__ = (UniqueConstraint("sequence_name", name="uq_number_sequence_name"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sequence_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    prefix: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    suffix: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    current_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    padding_length: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    reset_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="never")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)

__all__ = ["NumberSequence"]
