"""
HHMS MedicalDocument ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MedicalDocument(Base):
    """Clinical or administrative document linked to a patient."""

    __tablename__ = "MedicalDocument"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("Patient.id", name="fk_medical_document_patient"),
        nullable=False,
        index=True,
    )

    visit_id: Mapped[int | None] = mapped_column(
        ForeignKey("Visit.id", name="fk_medical_document_visit"),
        nullable=True,
        index=True,
    )

    admission_id: Mapped[int | None] = mapped_column(
        ForeignKey("Admission.id", name="fk_medical_document_admission"),
        nullable=True,
        index=True,
    )

    document_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    document_title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    file_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    document_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("User.id", name="fk_medical_document_uploaded_by"),
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


__all__ = ["MedicalDocument"]