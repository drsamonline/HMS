"""
Role ORM model for HHMS.

Represents a collection of permissions within the RBAC system.
Permissions are linked through the RolePermission association
table in a later package.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, UUIDPrimaryKeyMixin


class Role(
    Base,
    UUIDPrimaryKeyMixin,
    AuditMixin,
):
    """
    Role entity.

    Examples:
        Administrator
        Receptionist
        Doctor
        Pharmacist
        Laboratory Technician
    """

    __tablename__ = "roles"

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

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_system: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false",
    )

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation.
        """
        return (
            f"Role("
            f"id={self.id!s}, "
            f"code={self.code!r})"
        )


__all__ = [
    "Role",
]