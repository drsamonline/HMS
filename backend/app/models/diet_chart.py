"""HHMS Diet Chart ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DietChart(Base):
    """Compact diet chart linked to an inpatient admission."""

    __tablename__ = "DietChart"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admission_id: Mapped[int] = mapped_column(Integer, ForeignKey("Admission.id", name="fk_diet_chart_admission"), nullable=False, index=True)
    chart_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    diet_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    breakfast: Mapped[str | None] = mapped_column(Text, nullable=True)
    mid_morning: Mapped[str | None] = mapped_column(Text, nullable=True)
    lunch: Mapped[str | None] = mapped_column(Text, nullable=True)
    evening: Mapped[str | None] = mapped_column(Text, nullable=True)
    dinner: Mapped[str | None] = mapped_column(Text, nullable=True)
    special_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.id", name="fk_diet_chart_recorded_by"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow
    )

__all__ = ["DietChart"]
