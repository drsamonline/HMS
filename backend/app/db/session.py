"""
HHMS Database Session Management
================================

Provides the asynchronous SQLAlchemy engine, session factory,
and FastAPI database dependency used throughout HHMS.

The database layer is intentionally asynchronous because the
application's CRUD layer uses SQLAlchemy AsyncSession.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """
    Create and cache the asynchronous SQLAlchemy engine.

    Returns
    -------
    AsyncEngine
        Configured asynchronous SQLAlchemy engine.
    """

    settings = get_settings()

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Create and cache the asynchronous SQLAlchemy session factory.

    Returns
    -------
    async_sessionmaker[AsyncSession]
        Configured asynchronous session factory.
    """

    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session.

    Yields
    ------
    AsyncSession
        Active SQLAlchemy asynchronous session.

    Notes
    -----
    The session is closed automatically after the dependency
    lifecycle completes. Transaction commit/rollback decisions
    remain the responsibility of the service or request layer.
    """

    async with get_session_factory()() as db:
        yield db


__all__ = [
    "get_engine",
    "get_session_factory",
    "get_db",
]