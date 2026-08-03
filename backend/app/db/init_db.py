"""
HHMS Database Initialization

Provides helper functions for creating and dropping the database
schema during development and testing.

Production environments must use Alembic migrations instead of
these helper functions.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import get_engine

logger = logging.getLogger(__name__)


def create_database() -> None:
    """
    Create all registered database tables.

    Intended for development and testing only.
    """

    try:
        Base.metadata.create_all(bind=get_engine())
        logger.info("Database schema created successfully.")

    except SQLAlchemyError:
        logger.exception("Failed to create database schema.")
        raise


def drop_database() -> None:
    """
    Drop all registered database tables.

    Warning
    -------
    This permanently removes all application data.
    Never execute in a production environment.
    """

    try:
        Base.metadata.drop_all(bind=get_engine())
        logger.warning("Database schema dropped successfully.")

    except SQLAlchemyError:
        logger.exception("Failed to drop database schema.")
        raise