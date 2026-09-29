"""HHMS Pain Assessment ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PainAssessment(Base):
    """Compact pain assessment linked to an inpatient admission."""

    __tablename__ = "PainAssessment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admission_id: Mapped[int] = mapped_column(Integer, ForeignKey("Admission.id", name="fk_pain_assessment_admission"), nullable=False, index=True)
    assessment_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    pain_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    pain_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    site: Mapped[str | None] = mapped_column(String(200), nullable=True)
    character: Mapped[str | None] = mapped_column(String(200), nullable=True)
    aggravating_factors: Mapped[str | None] = mapped_column(Text, nullable=True)
    relieving_factors: Mapped[str | None] = mapped_column(Text, nullable=True)
    intervention: Mapped[str | None] = mapped_column(Text, nullable=True)
    reassessment_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.id", name="fk_pain_assessment_recorded_by"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

__all__ = ["PainAssessment"]
