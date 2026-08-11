"""
HHMS Investigation ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Investigation(Base):
    """Laboratory investigation requested for a patient."""

    __tablename__ = "Investigation"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("Patient.id", name="fk_investigation_patient"),
        nullable=False,
        index=True,
    )

    visit_id: Mapped[int | None] = mapped_column(
        ForeignKey("Visit.id", name="fk_investigation_visit"),
        nullable=True,
        index=True,
    )

    admission_id: Mapped[int | None] = mapped_column(
        ForeignKey("Admission.id", name="fk_investigation_admission"),
        nullable=True,
        index=True,
    )

    investigation_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    investigation_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    requested_by: Mapped[int] = mapped_column(
        ForeignKey("User.id", name="fk_investigation_requested_by"),
        nullable=False,
    )

    requested_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    investigation_status: Mapped[str] = mapped_column(
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


__all__ = ["Investigation"]