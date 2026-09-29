"""Permanent live-database references for physically archived laboratory data."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InvestigationArchiveReference(Base):
    """Retains investigation identity and lineage after the record leaves the live database."""

    __tablename__ = "InvestigationArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_investigation_id",
            name="uq_investigation_archive_ref_original_investigation",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_investigation_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_investigation_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Patient.id", name="fk_investigation_archive_ref_patient"),
        nullable=False,
        index=True,
    )
    visit_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    admission_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    investigation_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    investigation_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


__all__ = ["InvestigationArchiveReference"]
