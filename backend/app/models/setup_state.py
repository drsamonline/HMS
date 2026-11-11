"""First-run state.

Two facts live here: whether this installation has been set up, and the one-time
code that proves the person opening the wizard is standing at the server rather
than on the LAN.

The code exists because of a real hole. Without it, the first person to reach
`/setup` on a freshly installed server creates the administrator account - and on
a hospital LAN that is whoever gets there first, not necessarily whoever installed
it.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SetupState(Base):
    """One row, always id 1: this installation's first-run state."""

    __tablename__ = "SetupState"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    is_complete: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    #: SHA-256 of the setup code. The code itself is never stored, so reading the
    #: database does not give you the ability to claim the installation.
    code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    code_issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    code_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    #: Which wizard steps have been applied, as a comma-separated list of step
    #: keys. A list rather than a set of columns: the steps are a product
    #: decision and should not need a migration to change.
    steps_done: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


__all__ = ["SetupState"]
