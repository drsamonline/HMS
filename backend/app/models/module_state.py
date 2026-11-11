"""HHMS module enablement state.

Capability lives in `app.modules.registry`; this table holds only which modules
*this hospital* has switched on. One row per module, so a hospital that turns
pharmacy off and back on twice still has one row and an audit trail of who did it.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModuleState(Base):
    """Whether one module is enabled for this installation."""

    __tablename__ = "ModuleState"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    module_code: Mapped[str] = mapped_column(
        String(40), nullable=False, unique=True, index=True
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    enabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    enabled_by: Mapped[int | None] = mapped_column(nullable=True)
    disabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    disabled_by: Mapped[int | None] = mapped_column(nullable=True)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


__all__ = ["ModuleState"]
