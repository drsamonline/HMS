"""HHMS Diagnosis ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Diagnosis(Base):
    """Clinical diagnosis linked to a homoeopathic case record."""

    __tablename__ = "Diagnosis"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("CaseRecord.id", name="fk_diagnosis_case_record"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Patient.id", name="fk_diagnosis_patient"),
        nullable=False,
        index=True,
    )
    visit_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("Visit.id", name="fk_diagnosis_visit"),
        nullable=True,
        index=True,
    )
    diagnosis_name: Mapped[str] = mapped_column(String(200), nullable=False)
    diagnosis_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="clinical"
    )
    icd11_code: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    icd11_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    icd11_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icd11_release: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.id", name="fk_diagnosis_created_by"),
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


__all__ = ["Diagnosis"]
