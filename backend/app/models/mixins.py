"""
Reusable SQLAlchemy mixins for HHMS.

These mixins provide common database columns shared across
multiple ORM models.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """
    Adds a UUID primary key.

    Use this mixin for entities that require UUID-based
    primary keys.
    """

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class TimestampMixin:
    """
    Adds automatic creation and modification timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ActiveMixin:
    """
    Adds an active status flag.
    """

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )


class SoftDeleteMixin:
    """
    Adds soft-delete support.

    Records are marked as deleted without being physically
    removed from the database.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class AuditMixin(
    TimestampMixin,
    ActiveMixin,
):
    """
    Common audit fields shared by most entities.

    This mixin intentionally excludes the primary key so that
    each model can explicitly choose its identifier strategy.
    """


__all__ = [
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "ActiveMixin",
    "SoftDeleteMixin",
    "AuditMixin",
]