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

    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {
        "echo": settings.DATABASE_ECHO,
        "pool_pre_ping": True,
    }

    if settings.DATABASE_URL.startswith("sqlite+aiosqlite://"):
        connect_args["check_same_thread"] = False
        if ":memory:" in settings.DATABASE_URL:
            # In-memory SQLite exists only inside the single connection that
            # created it, so every session must share one pinned connection.
            from sqlalchemy.pool import StaticPool

            engine_kwargs["poolclass"] = StaticPool
        else:
            # File-based SQLite (the real packaged/LAN runtime) must support
            # concurrent requests.  A single pinned StaticPool connection
            # serialises *and* deadlocks multi-session workloads, so use one
            # connection per checkout plus WAL journaling and a busy timeout
            # below so simultaneous LAN clients can read/write safely.
            #
            # ``isolation_level=None`` puts the pysqlite driver in true
            # autocommit mode so SQLAlchemy (not the silent legacy driver
            # mode that auto-commits on DDL and never emits BEGIN for DML)
            # controls transaction boundaries.  Without this, row locks
            # acquired via ``SELECT ... FOR UPDATE`` (see
            # ``NumberSequenceService``) are released immediately and
            # concurrent identifier minting produces duplicate numbers.
            connect_args["isolation_level"] = None
        engine_kwargs["connect_args"] = connect_args
    else:
        engine_kwargs["connect_args"] = connect_args

    engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

    if (
        settings.DATABASE_URL.startswith("sqlite+aiosqlite://")
        and ":memory:" not in settings.DATABASE_URL
    ):
        # Per-connection pragmas for file-based SQLite: WAL lets concurrent
        # readers coexist with a writer, and busy_timeout makes transient
        # write-lock contention wait instead of failing with SQLITE_BUSY.
        from sqlalchemy import event

        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.execute("PRAGMA synchronous=NORMAL")
            finally:
                cursor.close()

    return engine


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