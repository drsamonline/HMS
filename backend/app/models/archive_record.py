"""HHMS Medical Records Department archive ORM model."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class ArchiveRecord(Base):
    """Archive event/location linked to an MRD patient file."""
    __tablename__ = "ArchiveRecord"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_file_id: Mapped[int] = mapped_column(
        ForeignKey("PatientFile.id", name="fk_archive_record_patient_file"),
        nullable=False, index=True,
    )
    archive_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archive_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    box_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retention_period: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
    )

__all__ = ["ArchiveRecord"]
