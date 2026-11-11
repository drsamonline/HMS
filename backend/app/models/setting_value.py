"""A setting changed from the interface, rather than from the environment.

Absence means "nothing has been changed here", so the effective value falls back
to the environment and then to the catalogue default. One row per key, replaced on
edit, with who changed it and when - because a hospital asking "who turned off
automatic backups" deserves an answer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SettingValue(Base):
    """One overridden setting."""

    __tablename__ = "SettingValue"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    setting_key: Mapped[str] = mapped_column(
        String(120), nullable=False, unique=True, index=True
    )

    #: Stored as text and coerced through the catalogue on read, so one column
    #: serves every type and a value is never reinterpreted by the database.
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)


__all__ = ["SettingValue"]
