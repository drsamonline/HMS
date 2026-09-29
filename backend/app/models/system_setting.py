"""HHMS system setting ORM model."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class SystemSetting(Base):
    __tablename__ = "SystemSetting"
    __table_args__ = (UniqueConstraint("setting_key", name="uq_system_setting_key"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    setting_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    setting_type: Mapped[str] = mapped_column(String(30), nullable=False, default="string")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_editable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

__all__ = ["SystemSetting"]
