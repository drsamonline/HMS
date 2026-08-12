"""HHMS Nutritional Assessment ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NutritionalAssessment(Base):
    """Compact nutritional assessment linked to an inpatient admission."""

    __tablename__ = "NutritionalAssessment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admission_id: Mapped[int] = mapped_column(Integer, ForeignKey("Admission.id", name="fk_nutritional_assessment_admission"), nullable=False, unique=True, index=True)
    assessment_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    appetite: Mapped[str | None] = mapped_column(String(30), nullable=True)
    dietary_pattern: Mapped[str | None] = mapped_column(String(100), nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(8,2), nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(8,2), nullable=True)
    bmi: Mapped[Decimal | None] = mapped_column(Numeric(6,2), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nutritional_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.id", name="fk_nutritional_assessment_recorded_by"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow
    )

__all__ = ["NutritionalAssessment"]
