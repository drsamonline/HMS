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
    current_value: int | str = 0,
    padding_length: int = 4,
    reset_frequency: str | None = "never",
) -> int:
    """Insert an active NumberSequence row and return its id.

    Required for end-to-end writes that mint human-readable identifiers
    (e.g. ``POST /patients`` needs the ``patient_number`` sequence).
    Must be called inside an active ``with make_client()`` block.

    ``current_value`` accepts ``None``/strings as well as ints so callers
    can probe how the API behaves on malformed persisted state; it is
    coerced to ``int`` before insertion. ``reset_frequency=None`` maps to
    the model default (``"never"``).
    """
    from app.db.session import get_session_factory
    from app.models.number_sequence import NumberSequence

    factory = get_session_factory()
    coerced_current = int(current_value or 0)
    frequency = reset_frequency if reset_frequency else "never"

    async def _seed() -> int:
        async with factory() as db:
            seq = NumberSequence(
                sequence_name=sequence_name,
                prefix=prefix,
                suffix=suffix,
                current_value=coerced_current,
                padding_length=padding_length,
                reset_frequency=frequency,
                is_active=True,
            )
            db.add(seq)
            await db.commit()
            await db.refresh(seq)
            return seq.id

    return asyncio.run(_seed())


def seed_visit(
    *,
    patient_id: int,
    consulting_doctor_id: int = 1,
    visit_type: str = "new",
    case_type: str = "new",
    chief_complaint: str | None = "QA integration complaint",
) -> tuple[int, str]:
    """Insert a Visit row directly and return ``(id, visit_number)``.

    Seeds the ``visit_number`` sequence when it is not configured yet so
    cross-module integration tests can chain Patient -> Visit -> OPD token
    flows without repeating boilerplate. Must be called inside an active
    ``with make_client()`` block.
    """
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models.number_sequence import NumberSequence
    from app.models.visit import Visit

    factory = get_session_factory()

    async def _seed() -> tuple[int, str]:
        async with factory() as db:
            seq = (
                await db.execute(
                    select(NumberSequence).where(
                        NumberSequence.sequence_name == "visit_number"
                    )
                )
            ).scalar_one_or_none()
            if seq is None:
                seq = NumberSequence(
                    sequence_name="visit_number",
                    prefix="V-",
                    suffix="",
                    current_value=0,
                    padding_length=4,
                    reset_frequency="never",
                    is_active=True,
                )
                db.add(seq)
                await db.flush()

            seq.current_value += 1
            now = datetime.now(timezone.utc)
            seq.updated_at = now
            visit_number = f"{seq.prefix}{str(seq.current_value).zfill(seq.padding_length)}{seq.suffix}"

            visit = Visit(
                patient_id=patient_id,
                visit_type=visit_type,
                visit_datetime=now,
                chief_complaint=chief_complaint,
                consultation_status="registered",
                consulting_doctor_id=consulting_doctor_id,
                case_type=case_type,
                visit_number=visit_number,
                visit_year=now.year,
                storage_tier="live",
                is_current_year=True,
            )
            db.add(visit)
            await db.commit()
            await db.refresh(visit)
            return visit.id, visit_number

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


def api_put(client, path: str, json=None, **kwargs):
    return client.put(
        f"/api/v1{path}", json=json, headers=auth_headers(), **kwargs
    )


__all__ = [
    "make_client",
    "auth_headers",
    "seed_user",
    "seed_number_sequence",
    "seed_visit",
    "api_get",
    "api_post",
    "api_patch",
    "api_put",
]
