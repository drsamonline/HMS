"""A medical certificate issued to a patient.

NCH Code of Ethics Regulation 7(1) requires a copy of every medical certificate to
be kept for at least three years. That makes the certificate a record with a life of
its own, not a printout - so it is stored, dated, and given a retention date at the
moment it is issued.

Regulation 27 requires a written case statement with a referral. A referral is a
kind of certificate here, and the case statement is required when it is that kind.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


#: The kinds a hospital issues. Referral is separate because it carries a duty the
#: others do not.
CERTIFICATE_TYPES = ("medical", "fitness", "absence", "referral")


class MedicalCertificate(Base):
    """One certificate, and how long it must be kept."""

    __tablename__ = "MedicalCertificate"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("Patient.id"), nullable=False, index=True
    )

    certificate_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    certificate_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    issued_by: Mapped[int] = mapped_column(Integer, nullable=False)

    #: The body of the certificate as issued. Stored rather than regenerated: a
    #: certificate is a statement made on a date, not a view of current data.
    content: Mapped[str] = mapped_column(Text, nullable=False)

    #: Regulation 27: required when the certificate is a referral.
    case_statement: Mapped[str | None] = mapped_column(Text, nullable=True)

    #: Regulation 7(1): issued_at plus three years, computed at issue and stored, so
    #: the obligation cannot drift with a settings change.
    retention_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    is_voided: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


__all__ = ["CERTIFICATE_TYPES", "MedicalCertificate"]
