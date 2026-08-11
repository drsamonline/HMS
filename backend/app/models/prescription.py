"""
HHMS Prescription ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Prescription(Base):
    """
    Clinical prescription issued during a Visit.
    """

    __tablename__ = "Prescription"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    visit_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Visit.id",
            name="fk_prescription_visit",
        ),
        nullable=False,
        index=True,
    )

    prescription_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    diagnosis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    clinical_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prescribed_by: Mapped[int] = mapped_column(
        ForeignKey(
            "User.id",
            name="fk_prescription_prescribed_by",
        ),
        nullable=False,
        index=True,
    )

    prescription_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    printed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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


__all__ = ["Prescription"]