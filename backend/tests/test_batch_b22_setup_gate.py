"""Gate tests for build-plan batch B22: the setup gate and the setup code.

The wizard runs before any user exists, so it cannot be permission guarded. What
replaces the permission is the setup code, and these tests are mostly about that
substitution being real: the code is needed, it locks out, and a login token cannot
stand in for it.
"""

from __future__ import annotations

import hashlib
import logging

import pytest


@pytest.fixture()
def isolated(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("HHMS_APPLICATION_ROOT", raising=False)

    from app.config import settings as settings_module
    from app.db import session as session_module

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()
    yield
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _client():
    from tests._qa_harness import make_client

    return make_client()


def _issue_code() -> str:
    """Read the code the status call logged, the way an installer would."""

    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models.setup_state import SetupState

    factory = get_session_factory()

    async def _read():
        async with factory() as db:
            row = (await db.execute(select(SetupState).limit(1))).scalar_one()
            return row.code_hash

    return asyncio.run(_read())


def _complete_setup_in_db() -> None:
    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models.setup_state import SetupState

    factory = get_session_factory()

    async def _go():
        async with factory() as db:
            row = (await db.execute(select(SetupState).limit(1))).scalar_one()
            row.is_complete = True
            row.code_hash = None
            await db.commit()

    asyncio.run(_go())


# ------------------------------------------------------------------- status
def test_a_fresh_installation_asks_to_be_set_up(isolated) -> None:
    with _client() as client:
        _clear_setup_state()
        response = client.get("/api/v1/setup/status")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["setup_required"] is True
    assert body["completed_steps"] == []
    assert len(body["steps"]) == 10


def _clear_setup_state() -> None:
    """Make the installation look new again.

    Two tests in one file share an in-memory database, so a code issued by one is
    still there for the next. This is the harness quirk noted at B20.
    """

    import asyncio

    from sqlalchemy import delete

    from app.db.session import get_session_factory
    from app.models.setup_state import SetupState

    factory = get_session_factory()

    async def _go():
        async with factory() as db:
            await db.execute(delete(SetupState))
            await db.commit()

    asyncio.run(_go())


def test_the_status_call_issues_a_code_to_the_log_and_nowhere_else(isolated, caplog) -> None:
    """Tested against the service, not through the HTTP client.

    The test client runs the application in another thread, which makes log
    capture a property of the harness rather than of the code. The service call is
    the thing being asserted: it logs the code and stores only its hash.
    """

    import asyncio

    from app.db.session import get_session_factory
    from app.services import setup

    emitted: list[str] = []
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        setup.logger, "warning", lambda message, *args, **kwargs: emitted.append(message % args)
    )

    try:
        with _client() as client:
            _clear_setup_state()

            factory = get_session_factory()

            async def _go():
                async with factory() as db:
                    result = await setup.status(db)
                    await db.commit()
                    return result

            body = asyncio.run(_go())
            stored = _issue_code()
    finally:
        monkeypatch.undo()

    # Asserted through the logger rather than through caplog: an earlier test in
    # the suite configures logging, after which propagation is off and caplog
    # stops seeing records. The property under test is that the code is emitted.
    assert emitted, "the setup code must be written to the server log"
    assert "setup code" in emitted[0].lower()
    assert body["setup_required"] is True
    assert stored, "only the hash is stored, and it must be stored"
    assert "code" not in body, "the status response must not carry the setup code"


def test_the_status_response_says_nothing_about_the_hospital(isolated) -> None:
    """A LAN client learns that the server is new, and nothing more."""

    with _client() as client:
        body = client.get("/api/v1/setup/status").json()

    assert set(body) == {"setup_required", "steps", "completed_steps", "locked_out"}


# ------------------------------------------------------------------- unlock
def test_a_wrong_code_is_refused(isolated) -> None:
    with _client() as client:
        _clear_setup_state()
        client.get("/api/v1/setup/status")
        response = client.post("/api/v1/setup/unlock", json={"code": "000000"})

    assert response.status_code == 403, response.text
    assert "attempts left" in response.json()["error"]["message"]


def test_the_code_locks_out_after_five_failures(isolated) -> None:
    with _client() as client:
        _clear_setup_state()
        client.get("/api/v1/setup/status")
        for _ in range(5):
            client.post("/api/v1/setup/unlock", json={"code": "000000"})

        response = client.post("/api/v1/setup/unlock", json={"code": "000000"})
        status = client.get("/api/v1/setup/status").json()

    assert response.status_code == 403
    assert "Too many wrong setup codes" in response.json()["error"]["message"]
    assert status["locked_out"] is True


def test_the_right_code_returns_a_setup_token(isolated) -> None:
    """The code is unknown to the test, so the stored hash is inverted to find it.

    A six-digit space is small: the test brute-forces the hash it can read, which
    is exactly what an attacker with database access could do - and the reason the
    code is stored hashed and locks out.
    """

    with _client() as client:
        _clear_setup_state()
        client.get("/api/v1/setup/status")
        stored = _issue_code()

        found = next(
            f"{candidate:06d}"
            for candidate in range(1_000_000)
            if hashlib.sha256(f"{candidate:06d}".encode()).hexdigest() == stored
        )

        response = client.post("/api/v1/setup/unlock", json={"code": found})

    assert response.status_code == 200, response.text
    assert response.json()["token"]
    assert response.json()["expires_in_minutes"] == 60


# ------------------------------------------------------- the token is scoped
def test_a_step_without_a_setup_token_is_refused(isolated) -> None:
    with _client() as client:
        response = client.post(
            "/api/v1/setup/steps/identity",
            json={"values": {"HOSPITAL_NAME": "Test Hospital"}},
        )
    assert response.status_code == 401, response.text


def test_a_login_token_cannot_finish_setup(isolated) -> None:
    """A setup token is not a login and a login is not a setup token."""

    from tests._qa_harness import auth_headers

    with _client() as client:
        response = client.post(
            "/api/v1/setup/steps/identity",
            headers=auth_headers(),
            json={"values": {"HOSPITAL_NAME": "Test Hospital"}},
        )

    assert response.status_code == 403, response.text
    assert "not a setup token" in response.json()["error"]["message"]


# ------------------------------------------------------------ a finished install
def test_a_finished_installation_refuses_to_unlock(isolated) -> None:
    with _client() as client:
        client.get("/api/v1/setup/status")
        _complete_setup_in_db()

        response = client.post("/api/v1/setup/unlock", json={"code": "123456"})
        status = client.get("/api/v1/setup/status").json()

    assert response.status_code == 403
    assert "already set up" in response.json()["error"]["message"]
    assert status["setup_required"] is False


def test_setup_cannot_finish_without_identity_and_people(isolated) -> None:
    """The two steps a hospital cannot work without."""

    import asyncio

    from app.auth.jwt import create_access_token

    token = create_access_token(
        subject="setup", additional_claims={"scope": "setup"}
    )
    headers = {"Authorization": f"Bearer {token}"}

    with _client() as client:
        response = client.post("/api/v1/setup/finish", headers=headers)

    assert response.status_code == 422, response.text
    assert "identity" in response.json()["error"]["message"]
