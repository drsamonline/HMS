"""Permanent live-database references for physically archived visits."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class VisitArchiveReference(Base):
    """Retains visit identity and lineage after the visit leaves the live database."""

    __tablename__ = "VisitArchiveReference"
    __table_args__ = (
        UniqueConstraint("original_visit_id", name="uq_visit_archive_ref_original_visit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_visit_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_visit_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Patient.id", name="fk_visit_archive_ref_patient"),
        nullable=False,
        index=True,
    )
    visit_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    visit_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


__all__ = ["VisitArchiveReference"]
