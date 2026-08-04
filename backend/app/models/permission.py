"""
Permission ORM model for HHMS.

Represents a single atomic permission within the RBAC system.
Permissions are assigned to roles through association tables.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, UUIDPrimaryKeyMixin


class Permission(
    Base,
    UUIDPrimaryKeyMixin,
    AuditMixin,
):
    """
    Permission entity.

    Examples:
        patient:create
        patient:read
        billing:approve
        inventory:issue
    """

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    module: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"Permission("
            f"id={self.id!s}, "
            f"code={self.code!r})"
        )


__all__ = [
    "Permission",
]