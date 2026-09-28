"""
HHMS Investigation ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
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

    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id", name="fk_investigation_department"),
        nullable=True,
        index=True,
    )

    service_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("department_services.id", name="fk_investigation_service"),
        nullable=True,
        index=True,
    )

    case_type: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
    )

    fulfillment_mode: Mapped[str | None] = mapped_column(
        String(20),
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

    investigation_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    storage_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="live",
        index=True,
    )

    is_current_year: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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