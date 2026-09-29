"""HHMS departmental service activity ledger."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ServiceActivity(Base):
    """One completed/requested departmental service activity for a patient.

    This ledger is intentionally generic so configurable departments such as
    laboratory, X-ray, physiotherapy and OGA can share one reporting source.
    """

    __tablename__ = "service_activities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("Patient.id", name="fk_service_activity_patient"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id", name="fk_service_activity_department"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "department_services.id",
            name="fk_service_activity_service",
        ),
        nullable=False,
        index=True,
    )
    activity_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    case_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="new", server_default="new", index=True
    )
    fulfillment_mode: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    source_type: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed", server_default="completed", index=True
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = ["ServiceActivity"]
