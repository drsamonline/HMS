"""
HHMS DispensingRecord ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DispensingRecord(Base):
    """
    Records dispensing of a MedicineBatch against a Prescription.
    """

    __tablename__ = "DispensingRecord"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    prescription_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "Prescription.id",
            name="fk_dispensing_record_prescription",
        ),
        nullable=False,
        index=True,
    )

    medicine_batch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "MedicineBatch.id",
            name="fk_dispensing_record_medicine_batch",
        ),
        nullable=False,
        index=True,
    )

    quantity_dispensed: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    dispensing_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    dispensed_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "User.id",
            name="fk_dispensing_record_user",
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
    "DispensingRecord",
]