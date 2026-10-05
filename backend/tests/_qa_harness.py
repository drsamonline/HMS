"""Batch 103 (Milestone 6) — Shared QA test harness.

Provides an in-memory SQLite + FastAPI ``TestClient`` environment so the
comprehensive-qa suite can exercise real HTTP routes end-to-end without
touching the production database file or running the app lifespan.

Usage::

    from _qa_harness import make_client, api_get, api_post

    with make_client() as client:
        assert api_get(client, "/health/live")["status"] == "ok"
"""
from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from typing import Iterator

# Configure environment BEFORE any ``app`` imports so cached settings
# resolve to the ephemeral in-memory database.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "batch103-qa-test-secret-key")
os.environ.setdefault("DISCOVERY_ENABLED", "false")


@contextmanager
def make_client() -> Iterator["object"]:
    """Yield a TestClient bound to the full API with an in-memory schema."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.v1.api import api_router
    from app.db.base import Base  # noqa: F401 - registers all models
    from app.db.session import get_engine, get_session_factory
    from app.middleware import (
        ProcessTimeMiddleware,
        RequestIDMiddleware,
        RequestLoggingMiddleware,
        register_exception_handlers,
    )

    # Fresh in-memory database per harness use: clear the cached engine so
    # every ``with make_client()`` block starts from an empty schema.
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    engine = get_engine()

    async def _create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(_create_schema())

    application = FastAPI()
    application.add_middleware(ProcessTimeMiddleware)
    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(application)
    application.include_router(api_router, prefix="/api/v1")

    client = TestClient(application)
    try:
        yield client
    finally:
        client.close()

        # Dispose the async engine from within an event loop so the
        # aiosqlite connections close cleanly (avoids MissingGreenlet).
        async def _dispose() -> None:
            await engine.dispose()

        asyncio.run(_dispose())
        get_session_factory.cache_clear()
        get_engine.cache_clear()


def auth_headers() -> dict[str, str]:
    """Return a bearer header carrying a valid signed JWT payload."""
    from app.auth.jwt import create_access_token

    token = create_access_token(subject="qa-batch103")
    return {"Authorization": f"Bearer {token}"}


def seed_user(*, username: str = "qa-admin", password: str = "qa-password") -> int:
    """Insert an active User row directly and return its id.

    Intended for end-to-end ``POST /auth/login`` round-trips against the
    ephemeral in-memory schema created by :func:`make_client`. Must be
    called inside an active ``with make_client()`` block.
    """
    from app.auth.password import hash_password
    from app.db.session import get_session_factory
    from app.models.user import User

    factory = get_session_factory()

    async def _seed() -> int:
        async with factory() as db:
            user = User(
                username=username,
                password_hash=hash_password(password),
                full_name="QA Batch 103",
                email=None,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user.id

    return asyncio.run(_seed())


def seed_number_sequence(
    *,
    sequence_name: str,
    prefix: str = "",
    suffix: str = "",
    current_value: int = 0,
    padding_length: int = 4,
    reset_frequency: str = "never",
) -> int:
    """Insert an active NumberSequence row and return its id.

    Required for end-to-end writes that mint human-readable identifiers
    (e.g. ``POST /patients`` needs the ``patient_number`` sequence).
    Must be called inside an active ``with make_client()`` block.
    """
    from app.db.session import get_session_factory
    from app.models.number_sequence import NumberSequence

    factory = get_session_factory()

    async def _seed() -> int:
        async with factory() as db:
            seq = NumberSequence(
                sequence_name=sequence_name,
                prefix=prefix,
                suffix=suffix,
                current_value=current_value,
                padding_length=padding_length,
                reset_frequency=reset_frequency,
                is_active=True,
            )
            db.add(seq)
            await db.commit()
            await db.refresh(seq)
            return seq.id

    return asyncio.run(_seed())


def api_get(client, path: str, **kwargs):
    return client.get(f"/api/v1{path}", headers=auth_headers(), **kwargs)


def api_post(client, path: str, json=None, **kwargs):
    return client.post(
        f"/api/v1{path}", json=json, headers=auth_headers(), **kwargs
    )


def api_patch(client, path: str, json=None, **kwargs):
    return client.patch(
        f"/api/v1{path}", json=json, headers=auth_headers(), **kwargs
    )


__all__ = [
    "make_client",
    "auth_headers",
    "api_get",
    "api_post",
    "api_patch",
]
