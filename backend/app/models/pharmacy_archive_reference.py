"""Permanent live-database references for physically archived pharmacy data."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DispenseArchiveReference(Base):
    """Retains dispense identity and lineage after the record leaves the live database."""

    __tablename__ = "DispenseArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_dispense_id", name="uq_dispense_archive_ref_original_dispense"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_dispense_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_dispense_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    prescription_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    dispense_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    medicine_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    quantity_dispensed: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    dispense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


__all__ = ["DispenseArchiveReference"]
