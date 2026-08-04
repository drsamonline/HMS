"""
Role-Permission association ORM model for HHMS.

Stores the active assignment of a permission to a role.
Historical changes are maintained separately by the audit
subsystem.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, UUIDPrimaryKeyMixin


class RolePermission(
    Base,
    UUIDPrimaryKeyMixin,
    AuditMixin,
):
    """
    Active assignment of a permission to a role.
    """

    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permissions_role_permission",
        ),
    )

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "roles.id",
            name="fk_role_permissions_role",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    permission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "permissions.id",
            name="fk_role_permissions_permission",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    assigned_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_role_permissions_assigned_by",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation.
        """
        return (
            "RolePermission("
            f"role_id={self.role_id}, "
            f"permission_id={self.permission_id}"
            ")"
        )


__all__ = [
    "RolePermission",
]