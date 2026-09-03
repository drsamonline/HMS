"""Permanent live-database references for physically archived case records."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CaseArchiveReference(Base):
    """Retains case identity and lineage after the case leaves the live database."""

    __tablename__ = "CaseArchiveReference"
    __table_args__ = (
        UniqueConstraint("original_case_id", name="uq_case_archive_ref_original_case"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_case_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_case_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Patient.id", name="fk_case_archive_ref_patient"),
        nullable=False,
        index=True,
    )
    case_family_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    case_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    archive_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


__all__ = ["CaseArchiveReference"]
