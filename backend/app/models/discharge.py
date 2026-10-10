"""
HHMS Discharge ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column


from app.models.base import Base


class Discharge(Base):
    """
    Discharge record for an inpatient Admission.
    """

    __tablename__ = "Discharge"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    admission_id: Mapped[int] = mapped_column(
        ForeignKey(
            "Admission.id",
            name="fk_discharge_admission",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    discharge_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    discharge_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    discharge_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    discharge_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    discharged_by: Mapped[int] = mapped_column(
        ForeignKey(
            "User.id",
            name="fk_discharge_user",
        ),
        nullable=False,
        index=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
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


__all__ = [
    "Discharge",
]