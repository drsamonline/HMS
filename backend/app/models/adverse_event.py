"""An adverse event to a homoeopathic product.

NCH Code of Ethics Regulation 37 requires adverse events to homoeopathic products
to be reported. That is a register, not a field: the event happens in the consulting
room, the report goes to the authority weeks later, and the gap between the two is
the thing a hospital is asked to evidence.

So the row records both moments - when it happened, and when it was reported - and
the readiness report counts the ones where the second is missing.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


#: How serious the event was. The three grades the reporting form asks for.
SEVERITIES = ("mild", "moderate", "severe")


class AdverseEvent(Base):
    """One adverse event, and whether it has been reported."""

    __tablename__ = "AdverseEvent"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("Patient.id"), nullable=False, index=True
    )
    medicine_id: Mapped[int | None] = mapped_column(
        ForeignKey("Medicine.id"), nullable=True, index=True
    )

    #: Free text, because the product may be a proprietary preparation the master
    #: list does not hold, and refusing to record it would lose the event.
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)

    event_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)

    reported: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    reported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reported_to: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reported_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    recorded_by: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


__all__ = ["SEVERITIES", "AdverseEvent"]
