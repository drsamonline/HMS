"""
User ORM model for HHMS.

Defines the application's internal user entity.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, UUIDPrimaryKeyMixin


class User(
    Base,
    UUIDPrimaryKeyMixin,
    AuditMixin,
):
    """
    Application user.

    Stores authentication identity and basic profile
    information.

    Relationships will be added in later packages.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation.
        """
        return (
            f"User("
            f"id={self.id!s}, "
            f"username={self.username!r})"
        )


__all__ = [
    "User",
]