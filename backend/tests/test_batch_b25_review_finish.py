"""Gate tests for build-plan batch B25: review, export and finish.

A wizard that applies as it goes and only shows a summary at the end is a wizard
nobody checks. The review is the step that makes the rest safe to click, so it is
tested as carefully as the finish.
"""

from __future__ import annotations

import pytest


@pytest.fixture()
def isolated(monkeypatch, tmp_path):
    root = tmp_path / "hhms-b25"
    root.mkdir()
    monkeypatch.setenv("HHMS_APPLICATION_ROOT", str(root))
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from app.config import runtime_paths as paths_module
    from app.config import settings as settings_module
    from app.db import session as session_module

    monkeypatch.setattr(paths_module, "application_root", lambda: root)
    monkeypatch.setattr(settings_module, "ROOT_DIR", root)
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()
    yield root
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _reset() -> None:
    import asyncio

    from sqlalchemy import delete

    import app.models as models
    from app.db.session import get_session_factory
    from app.models.setting_value import SettingValue
    from app.models.setup_state import SetupState

    factory = get_session_factory()

    async def _go():
        async with factory() as db:
            for model in (models.User, models.UserRole, models.Role, SettingValue, SetupState):
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
}


def _complete_mandatory(client) -> None:
    _step(client, "identity", {"HOSPITAL_NAME": "Anand Homoeopathy Hospital"})
    _step(client, "people", ADMIN)


# --------------------------------------------------------------------- review
def test_review_lists_every_step_with_what_is_done(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "identity", {"HOSPITAL_NAME": "Anand Homoeopathy Hospital"})
        review = client.get("/api/v1/setup/review", headers=_headers())

    assert review.status_code == 200, review.text
    body = review.json()
    assert len(body["steps"]) == 10
    by_step = {item["step"]: item for item in body["steps"]}
    assert by_step["identity"]["done"] is True
    assert by_step["people"]["done"] is False
    assert by_step["identity"]["values"]["HOSPITAL_NAME"] == "Anand Homoeopathy Hospital"


def test_review_names_the_mandatory_steps_still_missing(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        body = client.get("/api/v1/setup/review", headers=_headers()).json()

    assert body["missing"] == ["identity", "people"]


def test_review_needs_a_setup_token(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        assert client.get("/api/v1/setup/review").status_code == 401


# --------------------------------------------------------------------- export
def test_export_contains_the_answers_and_the_modules(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "identity", {"HOSPITAL_NAME": "Anand Homoeopathy Hospital"})
        _step(client, "modules", {"modules": ["pharmacy"]})
        exported = client.get("/api/v1/setup/export", headers=_headers()).json()

    assert exported["schema"] == 1
    assert exported["settings"]["HOSPITAL_NAME"] == "Anand Homoeopathy Hospital"
    assert "pharmacy" in exported["modules"]


# --------------------------------------------------------------------- finish
def test_finish_is_refused_until_the_mandatory_steps_are_done(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = client.post("/api/v1/setup/finish", headers=_headers())

    assert response.status_code == 422, response.text
    assert "identity" in response.json()["error"]["message"]


def test_finish_closes_setup(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _complete_mandatory(client)

        response = client.post("/api/v1/setup/finish", headers=_headers())
        status = client.get("/api/v1/setup/status").json()

    assert response.status_code == 200, response.text
    assert response.json()["setup_required"] is False
    assert status["setup_required"] is False


def test_finish_writes_the_staged_network_values_to_the_environment(isolated) -> None:
    """The staged values reach the only place the server reads them from."""

    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _complete_mandatory(client)
        _step(client, "network", {"SERVER_PORT": 8080, "DISCOVERY_NAME": "anand"})

        response = client.post("/api/v1/setup/finish", headers=_headers())

    assert response.status_code == 200, response.text
    assert response.json()["restart_required"] is True
    assert "SERVER_PORT" in response.json()["network_keys_written"]

    env_file = isolated / ".env"
    assert env_file.is_file()
    text = env_file.read_text()
    assert "SERVER_PORT=8080" in text
    assert "DISCOVERY_NAME=anand" in text


def test_finish_leaves_an_operators_own_environment_lines_alone(isolated) -> None:
    """Only the block between the markers is touched."""

    from tests._qa_harness import make_client

    (isolated / ".env").write_text("HHMS_OPERATOR_NOTE=keep me\n", encoding="utf-8")

    with make_client() as client:
        _reset()
        _complete_mandatory(client)
        _step(client, "network", {"SERVER_PORT": 8080})
        client.post("/api/v1/setup/finish", headers=_headers())

    text = (isolated / ".env").read_text()
    assert "HHMS_OPERATOR_NOTE=keep me" in text
    assert "SERVER_PORT=8080" in text


def test_finishing_twice_is_harmless(isolated) -> None:
    """The block is replaced, not appended, so a second run does not duplicate it."""

    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _complete_mandatory(client)
        _step(client, "network", {"SERVER_PORT": 8080})
        client.post("/api/v1/setup/finish", headers=_headers())
        client.post("/api/v1/setup/finish", headers=_headers())

    text = (isolated / ".env").read_text()
    assert text.count("SERVER_PORT=8080") == 1
    assert text.count("# >>> HHMS managed by the setup wizard >>>") == 1
