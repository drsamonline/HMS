"""B65 — the first run: the F-01 fix must not leave a fresh install with no way in.

F-01 removed the fallback to the well-known ``admin`` password, and that was right.
But the startup bootstrap still reached it by calling ``main([])`` with no password and
ignoring the refusal, so on a pristine database the boot printed the CLI's
``error: no password supplied`` - a message written for an operator who typed
something wrong - and left **zero accounts** behind. The module docstring, the
``run()`` comment and the smoke probe all still claimed the build shipped with
admin/admin, so nothing in the suite could see it: the smoke test took the count on
trust and passed.

These tests hold the two halves apart: no password means no account and a notice that
names the ways in; a configured password still bootstraps, so the headless install
keeps working.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


def _isolated_db(monkeypatch, tmp_path) -> None:
    """Point the whole process at a database that does not exist yet."""

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{(tmp_path / 'fresh.db').as_posix()}")
    monkeypatch.delenv("HHMS_ADMIN_INITIAL_PASSWORD", raising=False)
    monkeypatch.delenv("HHMS_BOOTSTRAP_DEFAULT_ADMIN", raising=False)

    from app.config import settings as settings_module
    from app.db import session as session_module

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _users() -> int:
    from app.cli.create_admin import count_users

    return count_users()


# ------------------------------------------------------- no password: no account
def test_a_fresh_database_with_no_password_gets_no_account(monkeypatch, tmp_path, capsys) -> None:
    """The whole point: the bootstrap refuses rather than reinstating the default."""

    _isolated_db(monkeypatch, tmp_path)
    from app.cli.create_admin import ensure_default_admin
    from app.startup import prepare_runtime

    prepare_runtime()
    assert ensure_default_admin() == 0
    assert _users() == 0


def test_the_fresh_install_is_told_what_to_do_instead(monkeypatch, tmp_path, capsys) -> None:
    """And it is a notice, not an error: the operator did nothing wrong."""

    _isolated_db(monkeypatch, tmp_path)
    from app.cli.create_admin import FIRST_RUN_NOTICE, ensure_default_admin
    from app.startup import prepare_runtime

    prepare_runtime()
    ensure_default_admin()
    out = capsys.readouterr()

    assert FIRST_RUN_NOTICE.strip() in out.out
    assert "/setup" in out.out
    assert "create-admin" in out.out
    assert "HHMS_ADMIN_INITIAL_PASSWORD" in out.out
    # The CLI's refusal is a different audience; it must not leak into a boot log
    # where it reads as a fault.
    assert "error: no password supplied" not in out.out
    assert "error: no password supplied" not in out.err


def test_a_fresh_install_can_still_be_entered_through_the_wizard(monkeypatch, tmp_path) -> None:
    """Zero accounts is only acceptable because /setup is open. Prove it is."""

    _isolated_db(monkeypatch, tmp_path)
    from app.cli.create_admin import ensure_default_admin
    from app.startup import prepare_runtime
    from tests._qa_harness import make_client

    prepare_runtime()
    ensure_default_admin()
    assert _users() == 0

    with make_client() as client:
        status = client.get("/api/v1/setup/status")

    assert status.status_code == 200, status.text
    assert status.json()["setup_required"] is True
    assert status.json()["locked_out"] is False


# ------------------------------------------------ a configured password: it works
def _stored_account() -> tuple[str, str, str | None]:
    """The one account in the database: username, password hash, role name."""

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models.role import Role
    from app.models.user import User
    from app.models.user_role import UserRole

    async def _read():
        factory = get_session_factory()
        async with factory() as db:
            user = await db.scalar(select(User))
            if user is None:
                return None
            role = await db.scalar(
                select(Role.role_name)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == user.id)
            )
            return user.username, user.password_hash, role

    return asyncio.run(_read())


def test_a_configured_password_still_bootstraps_the_account(monkeypatch, tmp_path) -> None:
    """The headless install path the CLI refusal points at must actually work.

    The stored hash is what is checked, not a login: the QA harness owns its own
    schema and rebuilds it, so an HTTP login here would test the harness rather
    than the bootstrap. ``verify_password`` against the configured secret is the
    same fact the login endpoint reads.
    """

    _isolated_db(monkeypatch, tmp_path)
    monkeypatch.setenv("HHMS_ADMIN_INITIAL_PASSWORD", "correct horse battery")
    from app.auth.password import verify_password
    from app.cli.create_admin import ensure_default_admin
    from app.startup import prepare_runtime

    prepare_runtime()
    assert ensure_default_admin() == 1

    account = _stored_account()
    assert account is not None
    username, password_hash, role = account
    assert username == "admin"
    assert role == "admin"
    assert verify_password("correct horse battery", password_hash) is True


def test_the_bootstrap_never_stores_the_well_known_password(monkeypatch, tmp_path) -> None:
    """F-01, restated where it could regress: no env, no flag, no admin/admin."""

    _isolated_db(monkeypatch, tmp_path)
    monkeypatch.setenv("HHMS_ADMIN_INITIAL_PASSWORD", "correct horse battery")
    from app.auth.password import verify_password
    from app.cli.create_admin import DEFAULT_BOOTSTRAP_PASSWORD, ensure_default_admin
    from app.startup import prepare_runtime

    prepare_runtime()
    ensure_default_admin()

    _, password_hash, _ = _stored_account()
    assert verify_password(DEFAULT_BOOTSTRAP_PASSWORD, password_hash) is False


def test_the_first_login_flag_is_set(monkeypatch, tmp_path) -> None:
    """The client is told to force a password change; that flag must exist."""

    _isolated_db(monkeypatch, tmp_path)
    monkeypatch.setenv("HHMS_ADMIN_INITIAL_PASSWORD", "correct horse battery")
    from sqlalchemy import select

    from app.cli.create_admin import FIRST_LOGIN_SETTING_KEY, ensure_default_admin
    from app.db.session import get_session_factory
    from app.models.system_setting import SystemSetting
    from app.startup import prepare_runtime

    prepare_runtime()
    ensure_default_admin()

    async def _read():
        factory = get_session_factory()
        async with factory() as db:
            return await db.scalar(
                select(SystemSetting).where(SystemSetting.setting_key == FIRST_LOGIN_SETTING_KEY)
            )

    setting = asyncio.run(_read())
    assert setting is not None
    assert setting.setting_value == "1"


# ------------------------------------------------------------------- idempotence
def test_a_second_boot_does_nothing(monkeypatch, tmp_path) -> None:
    _isolated_db(monkeypatch, tmp_path)
    monkeypatch.setenv("HHMS_ADMIN_INITIAL_PASSWORD", "correct horse battery")
    from app.auth.password import verify_password
    from app.cli.create_admin import ensure_default_admin
    from app.startup import prepare_runtime

    prepare_runtime()
    assert ensure_default_admin() == 1
    # A different password on the second boot must not overwrite the first.
    monkeypatch.setenv("HHMS_ADMIN_INITIAL_PASSWORD", "a different password")
    assert ensure_default_admin() == 1

    _, password_hash, _ = _stored_account()
    assert verify_password("correct horse battery", password_hash) is True


def test_the_bootstrap_can_be_switched_off(monkeypatch, tmp_path) -> None:
    _isolated_db(monkeypatch, tmp_path)
    monkeypatch.setenv("HHMS_ADMIN_INITIAL_PASSWORD", "correct horse battery")
    monkeypatch.setenv("HHMS_BOOTSTRAP_DEFAULT_ADMIN", "false")
    from app.cli.create_admin import ensure_default_admin
    from app.startup import prepare_runtime

    prepare_runtime()
    assert ensure_default_admin() == 0
    assert _users() == 0


# ------------------------------------------------- the smoke probe stops lying
def test_the_smoke_probe_refuses_a_build_with_no_way_in() -> None:
    """It used to print 'smoke-test ok' for a build nobody could log into."""

    source = (BACKEND / "app" / "server.py").read_text(encoding="utf-8")
    assert "_first_run_problem(port, user_count)" in source
    assert "user_count = ensure_default_admin()" in source


def test_the_probe_accepts_an_account_or_an_open_wizard() -> None:
    from app.server import _first_run_problem

    # An account exists: nothing to check against the server.
    assert _first_run_problem(9, 1) is None


def test_the_probe_reports_when_neither_exists() -> None:
    from app.server import _first_run_problem

    # Nothing is listening on port 9, and there are no accounts.
    problem = _first_run_problem(9, 0)
    assert problem is not None
    assert "no administrator account" in problem


def test_the_stale_claim_is_gone_from_the_code() -> None:
    """The docstrings said admin/admin was created at boot. It is not."""

    create_admin = (BACKEND / "app" / "cli" / "create_admin.py").read_text(encoding="utf-8")
    server = (BACKEND / "app" / "server.py").read_text(encoding="utf-8")
    for text in (create_admin, server):
        assert "logged into immediately with admin/admin" not in text
        assert "seed admin/admin so a fresh build is testable" not in text
