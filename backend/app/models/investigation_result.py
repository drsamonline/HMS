"""
HHMS InvestigationResult ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InvestigationResult(Base):
    """Final result recorded for a laboratory investigation."""

    __tablename__ = "InvestigationResult"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Investigation.id",
            name="fk_investigation_result_investigation",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    result_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    interpretation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    result_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    result_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    storage_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="live",
        index=True,
    )

    is_current_year: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    verified_by: Mapped[int | None] = mapped_column(
        ForeignKey(
            "User.id",
            name="fk_investigation_result_verified_by",
        ),
        nullable=True,
        index=True,
    )

    verification_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    report_status: Mapped[str] = mapped_column(
        String(20),
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


__all__ = ["InvestigationResult"]