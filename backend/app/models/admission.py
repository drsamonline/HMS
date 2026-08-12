"""
HHMS Admission ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Admission(Base):
    """
    Inpatient admission episode for a Patient.
    """

    __tablename__ = "Admission"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Patient.id",
            name="fk_admission_patient",
        ),
        nullable=False,
        index=True,
    )

    admission_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    admission_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    bed_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Bed.id",
            name="fk_admission_bed",
        ),
        nullable=False,
        index=True,
    )

    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id", name="fk_admission_department"),
        nullable=True,
        index=True,
    )

    service_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("department_services.id", name="fk_admission_service"),
        nullable=True,
        index=True,
    )

    case_type: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
    )

    admitted_by: Mapped[int] = mapped_column(
        ForeignKey(
            "User.id",
            name="fk_admission_user",
        ),
        nullable=False,
    )

    admission_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    admission_status: Mapped[str] = mapped_column(
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


__all__ = [
    "Admission",
]