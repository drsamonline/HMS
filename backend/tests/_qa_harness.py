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
from pathlib import Path
from typing import Iterator

# Configure environment BEFORE any ``app`` imports so cached settings
# resolve to the ephemeral in-memory database.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "batch103-qa-test-secret-key-0123456789abcdef")
os.environ.setdefault("DISCOVERY_ENABLED", "false")


def dashboard_source() -> str:
    """Every module that makes up the dashboard endpoints, as one string.

    B63 split the routes out of the computation: ``dashboard.py`` holds the builders,
    and ``reports_operational``/``reports_clinical``/``reports_financial`` hold the
    endpoints, one module per question the reports answer. A test that checks a route
    exists *and* that it calls a particular builder therefore has to read both, and
    doing that in twenty files by hand is how the next split gets forgotten.
    """

    root = Path(__file__).resolve().parents[2]
    parts = ("dashboard", "reports_operational", "reports_clinical", "reports_financial")
    return "".join(
        (root / "backend" / "app" / "api" / "v1" / "endpoints" / f"{name}.py").read_text(
            encoding="utf-8"
        )
        for name in parts
    )


#: One engine for the whole process, when the database is the in-memory default.
#:
#: Creating sixty tables eight hundred times was the entire cost of this suite: about
#: 2.5 seconds per ``make_client()`` block, none of it spent testing anything. An
#: in-memory database is created empty, so a block only needs the tables *emptied* -
#: which is a handful of DELETEs rather than sixty CREATEs.
#:
#: Anything that points the application at a different database (``make_file_client``)
#: invalidates this, because a shared engine that no longer matches the cached one is
#: exactly how the first attempt at this broke five tests.
_SHARED: dict = {"engine": None, "url": None, "ready": False}

IN_MEMORY_URL = "sqlite+aiosqlite:///:memory:"


def _invalidate_shared() -> None:
    """Forget the shared engine - called when the database URL changes."""

    _SHARED["engine"] = None
    _SHARED["url"] = None
    _SHARED["ready"] = False


def _acquire_engine():
    """The engine for this block, and whether it is the shared one."""

    from app.config.settings import get_settings
    from app.db.session import get_engine, get_session_factory

    url = os.environ.get("DATABASE_URL")

    if url != IN_MEMORY_URL:
        # Somebody pointed the app at a file. Give them their own engine and leave
        # the shared one alone; ``make_file_client`` invalidates it on the way out.
        get_settings.cache_clear()
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        return get_engine(), False

    # Ask the application which engine it will actually use, and share *that*.
    #
    # The distinction matters: a fixture elsewhere may call ``get_engine.cache_clear()``
    # to point the app at its own database and put it back afterwards. When it does,
    # the engine the app resolves is a new object, and holding an older one here would
    # leave the harness preparing a database the application never looks at - which is
    # exactly the failure that made the first attempt at this unshippable.
    engine = get_engine()

    if _SHARED["engine"] is not engine:
        _SHARED["engine"] = engine
        _SHARED["url"] = url
        _SHARED["ready"] = False

    return engine, True


async def _schema_is_current(connection) -> bool:
    """Whether the database has every table the models declare.

    A schema built once at the start of a process is only correct if every model was
    imported by then. One that was not - and one was not - leaves a table missing for
    the rest of the run, which reads as a bug in whatever happens to query it first.
    """

    from app.db.base import Base

    result = await connection.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    present = {row[0] for row in result.fetchall()}
    return set(Base.metadata.tables) <= present


async def _truncate(connection) -> None:
    """Empty every table, children first.

    Faster than dropping and recreating, and it keeps the schema the models describe
    rather than whatever an earlier module left behind.
    """

    from app.db.base import Base

    for table in reversed(Base.metadata.sorted_tables):
        await connection.execute(table.delete())


#: The ASGI stack is identical for every block, and assembling it costs about four
#: seconds - the second half of this suite's fixed cost. Built once per process.
#:
#: One thing does not survive that safely: the login throttle keeps its counters on
#: the middleware, so a cached application would accumulate every login the suite ever
#: makes and start refusing honest tests. The limiter is held here and reset per block.
_APPLICATION = None
_LIMITER = None


def _build_application():
    """Assemble the full production ASGI stack (middleware + handlers + api_router)."""

    global _APPLICATION
    if _APPLICATION is not None:
        return _APPLICATION
    from fastapi import FastAPI

    from app.api.v1.api import api_router
    from app.middleware import (
        ProcessTimeMiddleware,
        RateLimitMiddleware,
        RequestIDMiddleware,
        RequestLoggingMiddleware,
        register_exception_handlers,
    )

    application = FastAPI()
    application.add_middleware(ProcessTimeMiddleware)
    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(RequestLoggingMiddleware)

    # Mirror the production stack (Batch 109): login throttle active in
    # QA too, with a generous budget so legitimate suites (concurrent
    # LAN logins, repeated auth probes) never trip it. Settings are
    # resolved inside the harness env because ``get_settings`` is cached
    # per client block.
    from app.config.settings import get_settings as _get_settings
    from app.middleware.rate_limit import SlidingWindowRateLimiter

    global _LIMITER
    _settings = _get_settings()
    _LIMITER = SlidingWindowRateLimiter(
        limit=max(_settings.LOGIN_RATE_LIMIT_ATTEMPTS, 200),
        window_seconds=float(_settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS),
    )
    application.add_middleware(RateLimitMiddleware, limiter=_LIMITER)
    register_exception_handlers(application)
    application.include_router(api_router, prefix="/api/v1")
    _APPLICATION = application
    return application


@contextmanager
def make_client() -> Iterator["object"]:
    """Yield a TestClient bound to the full API with an in-memory schema."""
    from fastapi.testclient import TestClient

    from app.db.base import Base  # noqa: F401 - registers all models

    engine, shared = _acquire_engine()

    # Every block starts with a clean throttle, exactly as a fresh process would.
    if _LIMITER is not None:
        _LIMITER.reset()

    async def _prepare_schema() -> None:
        async with engine.begin() as connection:
            if shared and _SHARED["ready"] and await _schema_is_current(connection):
                # The tables exist and the schema is current: empty them.
                await _truncate(connection)
            else:
                # First block of the process, or a database that predates the
                # current models. Build it properly once.
                await connection.run_sync(Base.metadata.drop_all)
                await connection.run_sync(Base.metadata.create_all)
                if shared:
                    _SHARED["ready"] = True

    asyncio.run(_prepare_schema())
    _enable_every_module()

    application = _build_application()

    client = TestClient(application)
    try:
        yield client
    finally:
        client.close()

        if not shared:
            # A private engine: dispose it and clear the caches it populated, so the
            # next block starts from the default database rather than this one.
            async def _dispose() -> None:
                await engine.dispose()

            asyncio.run(_dispose())
            from app.config.settings import get_settings
            from app.db.session import get_engine, get_session_factory

            get_settings.cache_clear()
            get_session_factory.cache_clear()
            get_engine.cache_clear()


@contextmanager
def make_file_client(db_path: str) -> Iterator[tuple]:
    """Yield ``(client_factory, dispose)`` over one shared file-based SQLite DB.

    Reproduces the packaged LAN runtime: a file-backed database with WAL
    journaling and busy timeout, any number of independent ``TestClient``
    instances (one per simulated client machine), each built on its own
    event loop thread — exactly what concurrent multi-client requests hit
    on a real server process.

    The caller must invoke ``dispose()`` before exiting the context so the
    engine is torn down while the temporary DATABASE_URL env is still set.
    """
    from fastapi.testclient import TestClient

    from app.config.settings import get_settings
    from app.db.base import Base  # noqa: F401 - registers all models
    from app.db.session import get_engine, get_session_factory

    # The backup/restore endpoints operate on the *live* runtime data root,
    # so relocate HHMS_APPLICATION_ROOT to the temp directory for the
    # duration of the block (Batch 108).  The engine itself keeps serving
    # the caller-supplied DB path; BackupService._ensure_sqlite() resolves
    # the live file from DATABASE_URL.
    prev_app_root = os.environ.get("HHMS_APPLICATION_ROOT")
    prev_db_url = os.environ.get("DATABASE_URL")
    os.environ["HHMS_APPLICATION_ROOT"] = str(Path(db_path).resolve().parent)
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    get_settings.cache_clear()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    engine = get_engine()

    async def _create_schema() -> None:
        # drop_all first: create_all is checkfirst by default, so a database that
        # already exists - a file left by an earlier module, or an in-memory one
        # reused through a cached engine - would keep an older schema and every
        # query against a new column would fail. The block promises an empty
        # schema; this makes that true rather than hopeful.
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(_create_schema())
    _enable_every_module()

    application = _build_application()
    clients: list[TestClient] = []
    disposed = False

    def client_factory() -> TestClient:
        client = TestClient(application)
        clients.append(client)
        return client

    def dispose() -> None:
        nonlocal disposed
        if disposed:
            return
        disposed = True
        for client in clients:
            client.close()

        async def _dispose_engine() -> None:
            await engine.dispose()

        asyncio.run(_dispose_engine())
        get_settings.cache_clear()
        get_session_factory.cache_clear()
        get_engine.cache_clear()

    try:
        yield client_factory, dispose
    finally:
        # Safety net: dispose is idempotent, so this is a no-op when the
        # caller already invoked it inside the block — but guarantees the
        # pooled connections to this DB file are closed even if they
        # forgot (leaked engines caused cross-test state bleed in Batch 104).
        dispose()
        if prev_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev_db_url
        if prev_app_root is None:
            os.environ.pop("HHMS_APPLICATION_ROOT", None)
        else:
            os.environ["HHMS_APPLICATION_ROOT"] = prev_app_root

        # The shared in-memory engine no longer matches the cached one, so forget it.
        # A block that runs after this rebuilds rather than querying a database the
        # application is not looking at - which is how the first attempt at this
        # change broke five tests.
        _invalidate_shared()
        get_settings.cache_clear()


def _enable_every_module() -> None:
    """Turn every module on for a QA database.

    The harness builds its schema with ``create_all``, so the migration that seeds
    ``ModuleState`` never runs and every optional module would answer 404. An
    end-to-end suite exercises all of them, so all of them are on.
    """

    from app.db.session import get_session_factory
    from app.models.module_state import ModuleState
    from app.modules.registry import MODULES

    factory = get_session_factory()

    async def _run() -> None:
        from sqlalchemy import delete

        async with factory() as db:
            # Idempotent: a file-backed harness can be entered more than once
            # against the same database, and a second insert of the same module
            # would hit the unique constraint rather than being a no-op.
            await db.execute(delete(ModuleState))
            for module in MODULES:
                db.add(ModuleState(module_code=module.code, is_enabled=True))
            await db.commit()

    asyncio.run(_run())


#: The QA administrator. Every end-to-end suite needs one authenticated actor
#: whose permissions come from the database, because the guard resolves them
#: there rather than from the token (build plan B13/D-023).
QA_ADMIN_USERNAME = "qa-batch103"
QA_ADMIN_PASSWORD = "qa-password"


def _ensure_qa_admin() -> int:
    """Get or create the QA administrator, holding the administrator role."""

    from sqlalchemy import func, select

    from app.auth.password import hash_password
    from app.db.session import get_session_factory
    from app.models.role import Role
    from app.models.user import User
    from app.models.user_role import UserRole

    factory = get_session_factory()

    async def _run() -> int:
        async with factory() as db:
            user = (
                await db.execute(
                    select(User).where(User.username == QA_ADMIN_USERNAME)
                )
            ).scalar_one_or_none()
            if user is None:
                user = User(
                    username=QA_ADMIN_USERNAME,
                    password_hash=hash_password(QA_ADMIN_PASSWORD),
                    full_name="QA Administrator",
                    is_active=True,
                )
                db.add(user)
                await db.flush()

            role = (
                await db.execute(
                    select(Role).where(func.lower(Role.role_name) == "administrator")
                )
            ).scalar_one_or_none()
            if role is None:
                role = Role(role_name="administrator", description="Full access")
                db.add(role)
                await db.flush()

            link = (
                await db.execute(
                    select(UserRole).where(
                        UserRole.user_id == user.id, UserRole.role_id == role.id
                    )
                )
            ).scalar_one_or_none()
            if link is None:
                db.add(UserRole(user_id=user.id, role_id=role.id))

            await db.commit()
            return user.id

    return asyncio.run(_run())


def auth_headers() -> dict[str, str]:
    """Bearer header for the QA administrator, with a real user behind it.

    Before B14 this minted a token for a subject that was not an integer and
    belonged to no user. That worked while nothing checked permissions; once the
    guard resolves them from the database, a token with no user behind it is
    correctly refused.
    """
    from app.auth.jwt import create_access_token

    user_id = _ensure_qa_admin()
    token = create_access_token(
        subject=str(user_id),
        additional_claims={"username": QA_ADMIN_USERNAME, "roles": ["administrator"]},
    )
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
            await db.flush()

            # Give the seeded account the administrator role: a suite that logs
            # in through the real route needs an actor the guard will admit.
            from sqlalchemy import func, select

            from app.models.role import Role
            from app.models.user_role import UserRole

            role = (
                await db.execute(
                    select(Role).where(func.lower(Role.role_name) == "administrator")
                )
            ).scalar_one_or_none()
            if role is None:
                role = Role(role_name="administrator", description="Full access")
                db.add(role)
                await db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id))

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


# ---------------------------------------------------------------------------
# Batch 104 — multi-client LAN QA helpers
# ---------------------------------------------------------------------------

# Pre-computed Argon2 hash for the fixed LAN-QA password below.  Hashing is
# deliberately expensive; doing it once at import time (instead of per seed
# row) keeps concurrent fan-out tests fast and deterministic.
_QA_LAN_PASSWORD = "Lan-QA-Passw0rd!"
_QA_LAN_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "qKUZImbWH7QNiypH1Bxixg$"
    "NOBFOK8eHOnnEChxLCoK7tyTZC58loyU2ZMRfEleBN0"
)


def seed_client_user(index: int) -> tuple[str, str]:
    """Insert an active User row for simulated LAN client ``index``.

    Returns ``(username, password)`` so callers can perform real
    ``POST /auth/login`` round-trips against the shared file database.
    Must be called inside an active ``with make_file_client(...)`` block
    (after the engine env has been pointed at the shared DB).
    """
    from app.db.session import get_session_factory
    from app.models.user import User

    factory = get_session_factory()
    username = f"lan-client-{index:02d}"

    async def _seed() -> int:
        from sqlalchemy import func, select

        from app.models.role import Role
        from app.models.user_role import UserRole

        async with factory() as db:
            user = User(
                username=username,
                password_hash=_QA_LAN_HASH,
                full_name=f"LAN Client {index:02d}",
                email=None,
                is_active=True,
            )
            db.add(user)
            await db.flush()

            # A simulated LAN client is an administrator: the guard resolves
            # permissions from the database, so an account with no role can do
            # nothing, and this helper exists to exercise the routes.
            role = (
                await db.execute(
                    select(Role).where(func.lower(Role.role_name) == "administrator")
                )
            ).scalar_one_or_none()
            if role is None:
                role = Role(role_name="administrator", description="Full access")
                db.add(role)
                await db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id))

            await db.commit()
            await db.refresh(user)
            return user.id

    asyncio.run(_seed())
    return username, _QA_LAN_PASSWORD


def token_for_login(client, username: str, password: str) -> str:
    """Log in through the real auth route and return the bearer token."""
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    return body["access_token"]


def concurrent_map(fn, items, workers: int = 8) -> list:
    """Fan ``fn`` out over ``items`` across real threads (simulated LAN clients).

    Each worker thread performs its own blocking HTTP call through a
    TestClient; because every TestClient runs its own event loop on its own
    thread, this reproduces simultaneous multi-client traffic hitting one
    server process and one shared SQLite data file.
    """
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, items))


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
    "make_file_client",
    "auth_headers",
    "seed_user",
    "seed_number_sequence",
    "seed_visit",
    "seed_client_user",
    "token_for_login",
    "concurrent_map",
    "api_get",
    "api_post",
    "api_patch",
    "api_put",
]
