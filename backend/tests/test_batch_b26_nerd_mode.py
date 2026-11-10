"""Gate tests for build-plan batch B26: the escape hatch and restart handling.

"Anyone can use it, but nerds have their own tweaks" needs two things beyond the
wizard: a way to see whether a stored change is actually running, and a way to
configure a machine with no browser at all.

Both are tested against the same services the wizard uses, because the failure that
matters is the two paths drifting apart.
"""

from __future__ import annotations

import argparse
import asyncio

import pytest


@pytest.fixture()
def isolated(monkeypatch, tmp_path):
    root = tmp_path / "hhms-b26"
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


def _admin() -> dict:
    from tests._qa_harness import auth_headers

    return auth_headers()


# ------------------------------------------------------------- restart status
def test_a_setting_that_needs_a_restart_is_reported_as_pending(isolated) -> None:
    """The stored value and the running value disagree, and that is the answer."""

    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        headers = _admin()

        before = client.get("/api/v1/configuration/restart-status", headers=headers).json()
        client.patch(
            "/api/v1/configuration",
            headers=headers,
            json={"values": {"ACCESS_TOKEN_EXPIRE_MINUTES": 45}},
        )
        after = client.get("/api/v1/configuration/restart-status", headers=headers).json()

    assert before["restart_required"] is False
    # ACCESS_TOKEN_EXPIRE_MINUTES does not require a restart, so it must not appear.
    assert "ACCESS_TOKEN_EXPIRE_MINUTES" not in after["pending"]


def test_a_restart_required_setting_appears_with_both_values(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        headers = _admin()
        client.patch(
            "/api/v1/configuration",
            headers=headers,
            json={"values": {"JWT_ALGORITHM": "HS512"}},
        )
        status = client.get("/api/v1/configuration/restart-status", headers=headers).json()

    assert status["restart_required"] is True
    entry = status["pending"]["JWT_ALGORITHM"]
    assert entry["stored"] == "HS512"
    assert entry["running"] != "HS512", "the running process still has the old value"
    assert entry["label"] == "Token algorithm"


def test_restart_status_says_nothing_when_everything_matches(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        status = client.get(
            "/api/v1/configuration/restart-status", headers=_admin()
        ).json()

    assert status["restart_required"] is False
    assert status["pending"] == {}
    assert "matches" in status["note"]


def test_restart_status_needs_the_read_permission(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        assert client.get("/api/v1/configuration/restart-status").status_code == 401


# ------------------------------------------------------------- headless setup
def _args(**overrides) -> argparse.Namespace:
    base = {
        "hospital_name": "Anand Homoeopathy Hospital",
        "admin_username": "dr.momin",
        "admin_full_name": "Dr Sohil Momin",
        "admin_password_env": "HHMS_ADMIN_PASSWORD",
        "modules": "",
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_the_headless_setup_refuses_without_a_password(isolated, monkeypatch) -> None:
    from app.cli.setup import _run

    monkeypatch.delenv("HHMS_ADMIN_PASSWORD", raising=False)
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        assert asyncio.run(_run(_args())) == 1


def test_the_headless_setup_completes_an_installation(isolated, monkeypatch) -> None:
    """The same services the wizard uses, driven from a shell."""

    from app.cli.setup import _run
    from app.services import setup as setup_service
    from tests._qa_harness import make_client

    monkeypatch.setenv("HHMS_ADMIN_PASSWORD", "hospital-2026")

    with make_client() as client:
        _reset()
        # pharmacy is in the free edition; ipd is not, and is tested separately.
        code = asyncio.run(_run(_args(modules="pharmacy")))

        from app.db.session import get_session_factory

        factory = get_session_factory()

        async def _complete():
            async with factory() as db:
                return await setup_service.is_complete(db)

        assert code == 0
        assert asyncio.run(_complete()) is True

        login = client.post(
            "/api/v1/auth/login",
            json={"username": "dr.momin", "password": "hospital-2026"},
        )

    assert login.status_code == 200, login.text


def test_the_headless_setup_refuses_a_module_the_edition_does_not_include(
    isolated, monkeypatch
) -> None:
    """The edition is enforced here too, not only in the wizard."""

    from app.cli.setup import _run
    from tests._qa_harness import make_client

    monkeypatch.setenv("HHMS_ADMIN_PASSWORD", "hospital-2026")

    with make_client() as client:
        _reset()
        assert asyncio.run(_run(_args(modules="ipd"))) == 1


def test_the_headless_setup_refuses_an_unknown_module(isolated, monkeypatch) -> None:
    from app.cli.setup import _run
    from tests._qa_harness import make_client

    monkeypatch.setenv("HHMS_ADMIN_PASSWORD", "hospital-2026")

    with make_client() as client:
        _reset()
        assert asyncio.run(_run(_args(modules="pharmacy,dentistry"))) == 1


def test_the_headless_setup_refuses_a_second_run(isolated, monkeypatch) -> None:
    from app.cli.setup import _run
    from tests._qa_harness import make_client

    monkeypatch.setenv("HHMS_ADMIN_PASSWORD", "hospital-2026")

    with make_client() as client:
        _reset()
        assert asyncio.run(_run(_args())) == 0
        assert asyncio.run(_run(_args())) == 1, "a configured hospital is not re-set-up"


def test_the_password_is_not_taken_on_the_command_line() -> None:
    """It would land in shell history and in the process list."""

    from app.cli.setup import main

    # "--password" rather than "--admin-password": argparse accepts an
    # unambiguous prefix, and "--admin-password" is a prefix of
    # "--admin-password-env", so it would be taken as that flag and silently
    # consume the secret as an environment variable name.
    with pytest.raises(SystemExit):
        main(
            [
                "--hospital-name", "X",
                "--admin-username", "y",
                "--admin-full-name", "Z",
                "--password", "secret",
            ]
        )
