"""Gate tests for build-plan batch B50: the guided first run.

A new installation is a set of empty screens. The person who installed it knows what
they are doing; the receptionist who starts on Monday does not, and will not read a
manual before their first patient.

Two rules carry the design: the tutorial never touches a real patient, and progress is
read from the database rather than tracked in a browser.
"""

from __future__ import annotations

import pytest


def test_every_step_names_a_check_that_exists() -> None:
    """A step whose check does not exist can never be completed."""

    from app.core.tutorial import STEPS
    from app.services.tutorial import CHECKS

    missing = [step.code for step in STEPS if step.check not in CHECKS]
    assert not missing, f"steps with no check: {missing}"


def test_no_check_is_unused() -> None:
    from app.core.tutorial import STEPS
    from app.services.tutorial import CHECKS

    used = {step.check for step in STEPS}
    assert set(CHECKS) == used


def test_every_step_says_what_to_do_and_why() -> None:
    """A step that says what without why is an instruction nobody follows."""

    from app.core.tutorial import STEPS

    for step in STEPS:
        assert step.what.strip(), f"{step.code} says nothing to do"
        assert len(step.why) > 40, f"{step.code} does not say why it matters"


def test_every_step_opens_a_screen_that_exists() -> None:
    from app.core.tutorial import STEPS
    from app.modules.navigation import BY_VIEW

    unknown = [step.code for step in STEPS if step.view not in BY_VIEW]
    assert not unknown, f"steps pointing at screens that do not exist: {unknown}"


def test_the_steps_are_in_the_order_a_day_happens() -> None:
    from app.core.tutorial import STEPS

    assert [step.code for step in STEPS] == [
        "register",
        "visit",
        "prescribe",
        "bill",
        "print",
    ]


def test_the_tutorial_never_asks_anyone_to_practise_on_a_real_patient() -> None:
    """A tutorial that damages the record is not a tutorial."""

    from app.core.tutorial import STEPS

    text = " ".join(step.what + " " + step.why for step in STEPS).lower()
    assert "tutorial patient" in text
    # Nothing in the steps should ask the user to open an existing patient record.
    assert "existing patient" not in text


def test_progress_says_it_does_not_look_at_which_patient() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "tutorial.py"
    ).read_text(encoding="utf-8")
    assert "Nothing here looks at which patient you used" in source


# ------------------------------------------------------------------ endpoint
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


def test_a_fresh_installation_has_done_nothing(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        body = client.get("/api/v1/tutorial", headers=auth_headers()).json()

    assert body["completed"] == 0
    assert body["total"] == 5
    assert body["finished"] is False
    assert all(step["done"] is False for step in body["steps"])


def test_the_tutorial_needs_a_login_but_no_permission() -> None:
    """Everybody has a first day, including the administrator."""

    from app.dependencies.permissions import AUTHENTICATED_ONLY_PATHS, PUBLIC_PATHS

    assert "/api/v1/tutorial" in AUTHENTICATED_ONLY_PATHS
    assert "/api/v1/tutorial" not in PUBLIC_PATHS


# -------------------------------------------------------------------- client
def test_the_panel_is_dismissible() -> None:
    """A tutorial between a receptionist and a queue gets closed without reading."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "ui" / "tutorial.js"
    ).read_text(encoding="utf-8")
    assert "hhms_tutorial_hidden" in source
    assert "tutorialVisible" in source


def test_the_client_renders_what_the_server_says_is_done() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "ui" / "tutorial.js"
    ).read_text(encoding="utf-8")
    assert "step.done" in source
    assert "/api/v1/tutorial" in source


def test_the_client_escapes_the_step_text() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "ui" / "tutorial.js"
    ).read_text(encoding="utf-8")
    assert "escapeHtml(step.what)" in source
    assert "escapeHtml(step.why)" in source
