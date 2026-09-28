"""Permanent live-database references for physically archived IPD admission data."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdmissionArchiveReference(Base):
    """Retains admission identity and lineage after the episode leaves the live database."""

    __tablename__ = "AdmissionArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_admission_id", name="uq_admission_archive_ref_original_admission"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_admission_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_admission_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    admission_number: Mapped[str] = mapped_column(String(20), nullable=False)
    admission_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    bed_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    department_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    service_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    case_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    admitted_by: Mapped[int] = mapped_column(Integer, nullable=False)
    admission_status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


__all__ = ["AdmissionArchiveReference"]
