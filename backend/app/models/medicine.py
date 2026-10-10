"""
HHMS Medicine ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, String, Text, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Medicine(Base):
    """
    Pharmacy medicine master.
    """

    __tablename__ = "Medicine"

    __table_args__ = (
        UniqueConstraint(
            "medicine_name",
            name="uq_medicine_medicine_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    medicine_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    medicine_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    scientific_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    medicine_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
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


__all__ = ["Medicine"]