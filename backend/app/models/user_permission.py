"""
A permission granted to one person, on top of whatever their role gives them.

Roles cover the common case: a nurse is a nurse, a pharmacist is a pharmacist. The
exceptions are what eat an administrator's day - the locum covering billing for a
fortnight, the senior technician who also signs off reports, the matron who needs the
audit trail while the superintendent is on leave. Without this table those requests are
answered by widening a role, which quietly widens it for everybody.

ADDITIVE ONLY

A grant here adds a permission. It never removes one. Taking a permission away is done
by changing the role, where the change is visible to everyone it affects - not by
quietly editing one person's tick boxes. A per-user deny list is easy to build and
impossible to reason about six months later, and the person it surprises is the one
holding the pager.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserPermission(Base):
    """One permission granted directly to a user."""

    __tablename__ = "UserPermission"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_user_permission"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("User.id", ondelete="CASCADE"), nullable=False, index=True
    )
    #: The permission code, checked against the catalogue before it is written.
    code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)

    #: Who granted it. A permission granted by nobody is a permission nobody can explain.
    granted_by: Mapped[int | None] = mapped_column(
        ForeignKey("User.id", ondelete="SET NULL"), nullable=True
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    #: Nullable because most grants are permanent. Where it is set, the grant stops
    #: counting the moment it passes - a locum's fortnight ends without anybody
    #: remembering to take it away.
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    #: Why. One line, for the next person reading the audit trail.
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = ["UserPermission"]
