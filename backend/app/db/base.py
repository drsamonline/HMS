"""
HHMS Database Base
==================

Central database metadata interface for HHMS.

The application's authoritative SQLAlchemy declarative base is
defined in ``app.models.base``. This module re-exports that base
and metadata for database initialization and migration tooling.

Importing ``app.models`` also registers all currently implemented
ORM entities with the shared metadata.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.models import (
    NAMING_CONVENTION,
    Base,
    metadata,
)

__all__ = [
    "Base",
    "metadata",
    "NAMING_CONVENTION",
]