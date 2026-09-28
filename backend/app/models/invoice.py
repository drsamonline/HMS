"""
HHMS Invoice ORM Model.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Invoice(Base):
    """Billing invoice generated for a patient."""

    __tablename__ = "Invoice"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("Patient.id", name="fk_invoice_patient"),
        nullable=False,
        index=True,
    )

    visit_id: Mapped[int | None] = mapped_column(
        ForeignKey("Visit.id", name="fk_invoice_visit"),
        nullable=True,
    )

    admission_id: Mapped[int | None] = mapped_column(
        ForeignKey("Admission.id", name="fk_invoice_admission"),
        nullable=True,
    )

    invoice_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    invoice_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    storage_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="live",
        index=True,
    )

    is_current_year: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    generated_by: Mapped[int] = mapped_column(
        ForeignKey("User.id", name="fk_invoice_generated_by"),
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


__all__ = ["Invoice"]