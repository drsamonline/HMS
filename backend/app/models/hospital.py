"""HHMS Hospital configuration ORM model."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Hospital(Base):
    __tablename__ = "Hospital"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hospital_name: Mapped[str] = mapped_column(String(150), nullable=False)
    hospital_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    website: Mapped[str | None] = mapped_column(String(200), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    registration_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

__all__ = ["Hospital"]
