"""HHMS OPD token ORM model."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OPDToken(Base):
    """Queue token assigned to a patient's outpatient visit."""

    __tablename__ = "OPDToken"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    visit_id: Mapped[int] = mapped_column(
        ForeignKey("Visit.id", name="fk_opd_token_visit"),
        nullable=False,
        index=True,
    )
    token_number: Mapped[int] = mapped_column(Integer, nullable=False)
    queue_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    queue_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
    )


__all__ = ["OPDToken"]

