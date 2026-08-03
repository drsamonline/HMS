"""
HHMS Database Session Management

Provides the SQLAlchemy engine, session factory, and FastAPI
database dependency.

The engine and session factory are lazily initialized and cached
to improve startup behavior, testability, and future scalability.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Create and cache the SQLAlchemy engine.

    Returns
    -------
    Engine
        Configured SQLAlchemy engine.
    """

    settings = get_settings()

    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        future=True,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """
    Create and cache the SQLAlchemy session factory.

    Returns
    -------
    sessionmaker[Session]
        Configured SQLAlchemy session factory.
    """

    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI database dependency.

    Yields
    ------
    Session
        Active SQLAlchemy session.

    The session is automatically closed after use.
    """

    db = get_session_factory()()

    try:
        yield db

    finally:
        db.close()