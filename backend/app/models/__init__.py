"""
HHMS ORM model package.

This package exports the SQLAlchemy foundation used by all
future database models.

Business entities such as Patient, User, Appointment,
Department, Billing, etc. will inherit from these classes.
"""

from __future__ import annotations

from app.models.base import Base, NAMING_CONVENTION, metadata
from app.models.mixins import (
    ActiveMixin,
    AuditMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

__all__ = [
    "Base",
    "metadata",
    "NAMING_CONVENTION",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "ActiveMixin",
    "SoftDeleteMixin",
    "AuditMixin",
]