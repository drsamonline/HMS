"""Permanent live-database references for physically archived billing data."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InvoiceArchiveReference(Base):
    """Retains invoice identity and lineage after the invoice leaves the live database."""

    __tablename__ = "InvoiceArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_invoice_id", name="uq_invoice_archive_ref_original_invoice"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_invoice_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_invoice_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Patient.id", name="fk_invoice_archive_ref_patient"),
        nullable=False,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    invoice_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class PaymentArchiveReference(Base):
    """Retains payment identity and lineage after the payment leaves the live database."""

    __tablename__ = "PaymentArchiveReference"
    __table_args__ = (
        UniqueConstraint(
            "original_payment_id", name="uq_payment_archive_ref_original_payment"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_manifest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ArchiveManifest.id", name="fk_payment_archive_ref_manifest"),
        nullable=False,
        index=True,
    )
    original_payment_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    original_invoice_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    receipt_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    payment_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


__all__ = ["InvoiceArchiveReference", "PaymentArchiveReference"]
