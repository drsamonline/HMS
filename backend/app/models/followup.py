"""HHMS Homoeopathic Follow-up ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FollowUp(Base):
    """Longitudinal follow-up assessment for a case record."""

    __tablename__ = "FollowUp"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("CaseRecord.id", name="fk_followup_case_record"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Patient.id", name="fk_followup_patient"),
        nullable=False,
        index=True,
    )
    visit_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("Visit.id", name="fk_followup_visit"),
        nullable=True,
        index=True,
    )
    followup_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    general_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mental_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    particular_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    remedy_response: Mapped[str | None] = mapped_column(String(30), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    old_symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_prescription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("Prescription.id", name="fk_followup_previous_prescription"),
        nullable=True,
        index=True,
    )
    next_prescription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("Prescription.id", name="fk_followup_next_prescription"),
        nullable=True,
        index=True,
    )
    next_followup_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recorded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.id", name="fk_followup_recorded_by"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = ["FollowUp"]
