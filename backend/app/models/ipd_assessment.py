"""HHMS IPD Assessment ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IPDAssessment(Base):
    """Compact ipd assessment linked to an inpatient admission."""

    __tablename__ = "IPDAssessment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admission_id: Mapped[int] = mapped_column(Integer, ForeignKey("Admission.id", name="fk_ipd_assessment_admission"), nullable=False, unique=True, index=True)
    assessment_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    clinical_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    presenting_complaints: Mapped[str | None] = mapped_column(Text, nullable=True)
    history_present_illness: Mapped[str | None] = mapped_column(Text, nullable=True)
    general_examination: Mapped[str | None] = mapped_column(Text, nullable=True)
    systemic_examination: Mapped[str | None] = mapped_column(Text, nullable=True)
    initial_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.id", name="fk_ipd_assessment_recorded_by"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow
    )

__all__ = ["IPDAssessment"]
