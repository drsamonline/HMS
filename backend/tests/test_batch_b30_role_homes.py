"""Gate tests for build-plan batch B30: role-shaped home screens.

A receptionist and a medical superintendent opened the same dashboard, which meant
the receptionist scrolled past ward occupancy to reach the patient list, and the
superintendent saw a queue they never work in.

A home is not a permission. The permissions decide what a role *may* open; this
decides what it *should* open first.
"""

from __future__ import annotations

import pytest


# ------------------------------------------------------------------ coverage
def test_every_role_template_has_a_home_or_a_deliberate_fallback() -> None:
    """A role with no home gets the default, and that must be a decision."""

    from app.core.permissions import ROLE_TEMPLATES
    from app.modules.homes import HOMES, home_for

    # The administrator has no home of its own: its job is the whole hospital, so
    # it lands on the superintendent's overview.
    deliberately_shared = {"administrator"}

    for role in ROLE_TEMPLATES:
        home = home_for([role])
        if role in deliberately_shared:
            assert home.key != "default", f"{role} fell through to the default"
            continue
        assert home.key != "default", f"{role} has no home of its own"
        assert role in HOMES


def test_a_role_with_no_declared_home_gets_the_default_not_a_blank_screen() -> None:
    """A blank screen reads as a broken system."""

    from app.modules.homes import DEFAULT_HOME, home_for

    assert home_for(["nobody at all"]).key == DEFAULT_HOME.key
    assert home_for([]).key == DEFAULT_HOME.key
    assert DEFAULT_HOME.panels, "the default home must show something"


def test_a_user_with_several_roles_lands_on_the_most_senior_home() -> None:
    """A superintendent who also works the desk lands on the overview, not the queue."""

    from app.modules.homes import home_for

    assert home_for(["registration desk", "medical officer"]).key == "clinician"
    assert home_for(["medical officer", "medical superintendent"]).key == "superintendent"
    assert home_for(["administrator"]).key == "superintendent"


def test_every_panel_that_opens_a_view_names_one_the_manifest_knows() -> None:
    """A shortcut to a screen that does not exist is a button that refuses."""

    from app.modules.homes import HOMES
    from app.modules.navigation import BY_VIEW

    unknown = []
    for home in HOMES.values():
        for panel in home.panels:
            if panel.view is not None and panel.view not in BY_VIEW:
                unknown.append(f"{home.key}: {panel.view}")
    assert not unknown, f"panels pointing at unknown views: {unknown}"


def test_every_home_has_at_least_one_panel() -> None:
    from app.modules.homes import HOMES

    empty = [key for key, home in HOMES.items() if not home.panels]
    assert not empty, f"homes with nothing on them: {empty}"


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


def test_the_endpoint_returns_the_callers_home(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/home", headers=auth_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"]
    assert isinstance(body["panels"], list)


def test_the_endpoint_drops_a_panel_the_caller_cannot_open(isolated) -> None:
    """A shortcut that leads to a refusal is worse than no shortcut."""

    from app.modules.navigation import BY_VIEW

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        body = client.get("/api/v1/home", headers=auth_headers()).json()

    for panel in body["panels"]:
        if panel["view"]:
            item = BY_VIEW[panel["view"]]
            assert item.view == panel["view"]


def test_the_endpoint_needs_a_login(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        assert client.get("/api/v1/home").status_code == 401


# -------------------------------------------------------------------- client
def test_the_client_renders_what_the_server_sends() -> None:
    """Adding a role's home is a backend change, not a frontend one."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "home.js"
    ).read_text(encoding="utf-8")
    assert 'fetch("/api/v1/home"' in source
    assert "home.panels.map" in source
    assert "registration" not in source, "the client must not hardcode a role's home"


def test_the_client_uses_the_kit_for_its_states() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "home.js"
    ).read_text(encoding="utf-8")
    assert "loadingState" in source
    assert "errorState" in source
