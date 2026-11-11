"""Gate tests for build-plan batch B24: the people and network steps.

The people step is the handover: before it every write went through the setup
token, after it there is a person who can log in. That handover is the thing worth
testing, so most of this file is about a login actually working afterwards.
"""

from __future__ import annotations

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


def _reset() -> None:
    import asyncio

    from sqlalchemy import delete

    import app.models as models
    from app.db.session import get_session_factory
    from app.models.setup_state import SetupState

    factory = get_session_factory()

    async def _go():
        async with factory() as db:
            for model in (models.User, models.UserRole, models.Role, SetupState):
                await db.execute(delete(model))
            await db.commit()

    asyncio.run(_go())


def _headers() -> dict:
    from app.auth.jwt import create_access_token

    token = create_access_token(subject="setup", additional_claims={"scope": "setup"})
    return {"Authorization": f"Bearer {token}"}


def _step(client, step: str, values: dict):
    return client.post(
        f"/api/v1/setup/steps/{step}", headers=_headers(), json={"values": values}
    )


ADMIN = {
    "username": "dr.momin",
    "password": "hospital-2026",
    "full_name": "Dr Sohil Momin",
    "email": "sohil@example.in",
}


# --------------------------------------------------------------------- people
def test_the_people_step_creates_an_administrator(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "people", ADMIN)

    assert response.status_code == 200, response.text
    assert response.json()["user_created"] is True
    assert response.json()["username"] == "dr.momin"


def test_the_administrator_can_log_in_afterwards(isolated) -> None:
    """The handover: the setup token's job ends when a person can log in."""

    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "people", ADMIN)

        response = client.post(
            "/api/v1/auth/login",
            json={"username": ADMIN["username"], "password": ADMIN["password"]},
        )

    assert response.status_code == 200, response.text
    assert response.json()["access_token"]


def test_the_administrator_can_actually_do_something(isolated) -> None:
    """A login that cannot open a screen is not a handover."""

    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "people", ADMIN)

        login = client.post(
            "/api/v1/auth/login",
            json={"username": ADMIN["username"], "password": ADMIN["password"]},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        patients = client.get("/api/v1/patients", headers=headers)
        menu = client.get("/api/v1/navigation", headers=headers)

    assert patients.status_code == 200, patients.text
    assert menu.status_code == 200, menu.text
    assert len(menu.json()) > 5


def test_a_short_password_is_refused(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "people", {**ADMIN, "password": "short"})

    assert response.status_code == 422, response.text
    assert "8 characters" in response.json()["error"]["message"]


def test_the_people_step_is_idempotent(isolated) -> None:
    """A second click must not create a second administrator or reset a password."""

    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "people", ADMIN)
        second = _step(client, "people", {**ADMIN, "password": "different-2026"})

        login = client.post(
            "/api/v1/auth/login",
            json={"username": ADMIN["username"], "password": ADMIN["password"]},
        )

    assert second.status_code == 200, second.text
    assert second.json()["user_created"] is False
    assert login.status_code == 200, "the original password must still work"


# -------------------------------------------------------------------- network
def test_network_values_are_staged_not_applied(isolated) -> None:
    """They are read before the database opens, so they cannot be stored in it."""

    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "network", {"SERVER_PORT": 8080})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["staged"] == {"SERVER_PORT": 8080}
    assert body["restart_required"] is True
    assert "restarts" in body["note"]


def test_an_out_of_range_port_is_refused(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "network", {"SERVER_PORT": 80})

    assert response.status_code == 422, response.text
    assert "between 1024 and 65535" in response.json()["error"]["message"]


def test_an_empty_discovery_name_is_refused(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "network", {"DISCOVERY_NAME": "  "})

    assert response.status_code == 422, response.text


# ----------------------------------------------------------------------- data
def test_the_data_step_writes_settings(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "data", {"LIVE_DATA_YEARS": 2})

    assert response.status_code == 200, response.text
    assert "data" in response.json()["completed_steps"]
