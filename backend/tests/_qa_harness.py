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

import os
from contextlib import asynccontextmanager, contextmanager
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
    with engine.begin() as connection:
        connection.run_sync(Base.metadata.create_all)

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
        engine.sync_engine.dispose()
        get_session_factory.cache_clear()
        get_engine.cache_clear()


def auth_headers() -> dict[str, str]:
    """Return a bearer header carrying a valid signed JWT payload."""
    from app.auth.jwt import create_access_token

    token = create_access_token(subject="qa-batch103")
    return {"Authorization": f"Bearer {token}"}


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
