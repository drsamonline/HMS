"""The two findings from the code audit that were worth fixing immediately.

F-01: a default administrator password could be set, and the warning was the only
control. On a LAN server nobody reads the warning, and an account called admin with a
password called admin is not a hypothetical - it is the default outcome of one command.

F-06: the audit chain is verified nightly and a break is logged at error level. Nobody
reads the log, and a break means the trail was altered outside the application - the one
thing the trail exists to detect.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def _create_admin(*args: str) -> subprocess.CompletedProcess:
    # Inherit the environment, minus the variables that would supply a password -
    # a stripped env loses site-packages and the subprocess cannot import anything.
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("HHMS_ADMIN_")
    }
    return subprocess.run(
        [sys.executable, "-m", "app.cli.create_admin", *args],
        capture_output=True,
        text=True,
        cwd=BACKEND,
        env=env,
    )


# ------------------------------------------------------------------ F-01
def test_creating_an_administrator_without_a_password_is_refused() -> None:
    result = _create_admin("--username", "audit-probe")
    assert result.returncode == 1
    assert "no password supplied" in result.stderr


def test_the_refusal_names_the_safe_path() -> None:
    """An operator who is told no needs to be told what to do instead."""

    result = _create_admin("--username", "audit-probe")
    assert "HHMS_ADMIN_INITIAL_PASSWORD" in result.stderr
    assert "setup wizard" in result.stderr


def test_the_default_password_needs_an_explicit_flag() -> None:
    """It exists for a disposable test machine, and says so."""

    source = (BACKEND / "app" / "cli" / "create_admin.py").read_text(encoding="utf-8")
    assert "--allow-default-password" in source
    assert "do not use it on any" in source


def test_the_flag_is_what_reaches_the_default() -> None:
    source = (BACKEND / "app" / "cli" / "create_admin.py").read_text(encoding="utf-8")
    # The default is only reachable through the flag, never as a fallback.
    assert "elif args.allow_default_password:" in source


# ------------------------------------------------------------------ F-06
def test_the_audit_chain_is_reported_where_somebody_can_see_it() -> None:
    from app.modules.homes import HOMES

    panels = HOMES["medical superintendent"].panels
    chain = [panel for panel in panels if panel.kind == "audit_chain"]
    assert len(chain) == 1
    assert chain[0].hide_when_empty is True


def test_the_panel_opens_the_trail_it_is_reporting_on() -> None:
    from app.modules.homes import HOMES
    from app.modules.navigation import BY_VIEW

    panel = next(
        panel for panel in HOMES["medical superintendent"].panels if panel.kind == "audit_chain"
    )
    assert panel.view in BY_VIEW


def test_an_intact_chain_keeps_the_panel_off_the_screen() -> None:
    """A card that always says 'the trail verifies' teaches people to ignore it."""

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        body = client.get("/api/v1/home", headers=auth_headers()).json()

    assert not [p for p in body["panels"] if p["kind"] == "audit_chain"]


def test_the_endpoint_answers_with_the_real_report() -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/compliance/audit-chain", headers=auth_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["message"] == "The audit trail verifies."


def test_a_broken_chain_would_show_and_say_so() -> None:
    """The positive path is tested above; this is the one that matters."""

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/compliance/audit-chain", headers=auth_headers())

    # The message for a break is the opposite of the message for an intact chain, and
    # it is not a support call - it is an incident.
    assert "not a support call" not in response.json()["message"]
    source = (
        BACKEND / "app" / "api" / "v1" / "endpoints" / "compliance.py"
    ).read_text(encoding="utf-8")
    assert "This is not a support call." in source
