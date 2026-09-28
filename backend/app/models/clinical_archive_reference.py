"""Permanent live-database references for physically archived clinical prescriptions."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PrescriptionArchiveReference(Base):
    """Retains prescription identity and visit lineage after the record leaves the live database."""

    __tablename__ = "PrescriptionArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_prescription_id",
            name="uq_prescription_archive_ref_original_prescription",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_prescription_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_prescription_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    visit_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    prescription_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    prescription_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


class PrescriptionItemArchiveReference(Base):
    """Retains prescription-item identity and dispensing lineage after archival."""

    __tablename__ = "PrescriptionItemArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_item_id",
            name="uq_prescription_item_archive_ref_original_item",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_prescription_item_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_item_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    original_prescription_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    medicine_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    item_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )


__all__ = [
    "PrescriptionArchiveReference",
    "PrescriptionItemArchiveReference",
]
