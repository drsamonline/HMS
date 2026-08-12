"""HHMS Homoeopathic Case Record ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CaseRecord(Base):
    """Compact, longitudinal homoeopathic case record."""

    __tablename__ = "CaseRecord"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Patient.id", name="fk_case_record_patient"),
        nullable=False,
        index=True,
    )
    visit_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("Visit.id", name="fk_case_record_visit"),
        nullable=True,
        index=True,
    )
    admission_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("Admission.id", name="fk_case_record_admission"),
        nullable=True,
        index=True,
    )
    case_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    case_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )

    chief_complaints: Mapped[str | None] = mapped_column(Text, nullable=True)
    history_present_illness: Mapped[str | None] = mapped_column(Text, nullable=True)
    past_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    personal_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    mental_generals: Mapped[str | None] = mapped_column(Text, nullable=True)
    physical_generals: Mapped[str | None] = mapped_column(Text, nullable=True)
    particulars: Mapped[str | None] = mapped_column(Text, nullable=True)
    female_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    male_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    sexual_reproductive_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    obstetric_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    surgical_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_examination: Mapped[str | None] = mapped_column(Text, nullable=True)
    totality: Mapped[str | None] = mapped_column(Text, nullable=True)
    characteristic_symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    miasmatic_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    analytical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    remedy_differential: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescribing_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    quick_generals: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    modalities: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )

    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.id", name="fk_case_record_created_by"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
    )


__all__ = ["CaseRecord"]
