"""
SQLAlchemy declarative base for HHMS.

This module provides the application's declarative base class
and metadata naming conventions for consistent database object
naming and Alembic compatibility.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": (
        "fk_%(table_name)s_"
        "%(column_0_name)s_"
        "%(referred_table_name)s"
    ),
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(
    naming_convention=NAMING_CONVENTION,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Every database model in HHMS must inherit from this class.
    """

    metadata = metadata


__all__ = [
    "Base",
    "metadata",
    "NAMING_CONVENTION",
]