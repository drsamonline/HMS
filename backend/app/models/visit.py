"""
HHMS Visit ORM Model.

Implements the Visit table defined in DATABASE_SCHEMA.md.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Visit(Base):
    """
    Clinical encounter between a Patient and the hospital.
    """

    __tablename__ = "Visit"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "Patient.id",
            name="fk_visit_patient",
        ),
        nullable=False,
        index=True,
    )

    visit_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    visit_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    visit_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    chief_complaint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    consultation_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id", name="fk_visit_department"),
        nullable=True,
        index=True,
    )

    service_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("department_services.id", name="fk_visit_service"),
        nullable=True,
        index=True,
    )

    case_type: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
    )

    consulting_doctor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "User.id",
            name="fk_visit_consulting_doctor",
        ),
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
        server_default="CURRENT_TIMESTAMP",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
    )


__all__ = [
    "Visit",
]