"""
User-Role association ORM model for HHMS.

Stores the active assignment of a role to a user.
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


class UserRole(
    Base,
    UUIDPrimaryKeyMixin,
    AuditMixin,
):
    """
    Active assignment of a role to a user.
    """

    __tablename__ = "user_roles"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            name="uq_user_roles_user_role",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_user_roles_user",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "roles.id",
            name="fk_user_roles_role",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    assigned_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_user_roles_assigned_by",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation.
        """
        return (
            "UserRole("
            f"user_id={self.user_id}, "
            f"role_id={self.role_id}"
            ")"
        )


__all__ = [
    "UserRole",
]