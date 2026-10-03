"""
HHMS Database Package
=====================

Public exports for the asynchronous HHMS database layer.

The package exposes the authoritative SQLAlchemy metadata,
asynchronous engine/session factories, database dependency,
and development/testing schema helpers.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from .base import (
    NAMING_CONVENTION,
    Base,
    metadata,
)
from .init_db import (
    create_database,
    drop_database,
)
from .session import (
    get_db,
    get_engine,
    get_session_factory,
)

__all__ = [
    # SQLAlchemy metadata
    "Base",
    "metadata",
    "NAMING_CONVENTION",

    # Asynchronous database infrastructure
    "get_engine",
    "get_session_factory",
    "get_db",

    # Development/testing schema helpers
    "create_database",
    "drop_database",
]