"""
HHMS Database Initialization
============================

Provides asynchronous helpers for creating and dropping the
registered SQLAlchemy database schema during development and
testing.

Production schema changes must be managed through Alembic
migrations rather than these helper functions.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import get_engine


logger = logging.getLogger("HHMS")


async def create_database() -> None:
    """
    Create all registered database tables.

    This helper is intended for development and testing.
    Production deployments should use Alembic migrations.

    Raises
    ------
    SQLAlchemyError
        If schema creation fails.
    """

    engine = get_engine()

    try:
        async with engine.begin() as connection:
            await connection.run_sync(
                Base.metadata.create_all,
            )

        logger.info(
            "Database schema created successfully."
        )

    except SQLAlchemyError:
        logger.exception(
            "Failed to create database schema."
        )
        raise


async def drop_database() -> None:
    """
    Drop all registered database tables.

    Warning
    -------
    This permanently removes all application data and must
    never be executed against a production database.

    Raises
    ------
    SQLAlchemyError
        If schema removal fails.
    """

    engine = get_engine()

    try:
        async with engine.begin() as connection:
            await connection.run_sync(
                Base.metadata.drop_all,
            )

        logger.warning(
            "Database schema dropped successfully."
        )

    except SQLAlchemyError:
        logger.exception(
            "Failed to drop database schema."
        )
        raise


__all__ = [
    "create_database",
    "drop_database",
]