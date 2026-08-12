"""HHMS Medical Records Department patient-file ORM model."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class PatientFile(Base):
    """Administrative MRD file/index linked to a patient."""
    __tablename__ = "PatientFile"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("Patient.id", name="fk_patient_file_patient"),
        nullable=False, index=True,
    )
    file_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    shelf_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rack_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
    )

__all__ = ["PatientFile"]
