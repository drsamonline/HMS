"""Gate tests for build-plan batch B48: in-app help.

The guidance already existed in the role guides and the runbook. What was missing was
having it where the person is, at the moment they are stuck, rather than in a document
nobody opens on a busy morning.

The property that matters: every screen has help, and the help is about that screen.
"""

from __future__ import annotations

import pytest

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
HELP = ROOT / "docs" / "help"


def test_every_screen_in_the_menu_has_a_help_topic() -> None:
    """A screen with no help is a screen where somebody guesses."""

    from app.modules.navigation import NAV_ITEMS

    missing = [item.view for item in NAV_ITEMS if not (HELP / f"{item.view}.md").is_file()]
    assert not missing, f"screens with no help: {missing}"


def test_no_help_topic_belongs_to_a_screen_that_does_not_exist() -> None:
    """A topic for a renamed screen is a document nobody will ever read."""

    from app.modules.navigation import NAV_ITEMS

    views = {item.view for item in NAV_ITEMS}
    orphans = [path.stem for path in HELP.glob("*.md") if path.stem not in views]
    assert not orphans, f"help topics for screens that do not exist: {orphans}"


def test_every_topic_has_a_title_and_a_body() -> None:
    for path in sorted(HELP.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# "), f"{path.name} has no title"
        body = "\n".join(text.splitlines()[1:]).strip()
        assert len(body) > 120, f"{path.name} is too thin to help anybody"


def test_the_help_service_finds_every_topic() -> None:
    from app.services import help

    topics = help.available()
    assert len(topics) >= 14
    assert "patients" in topics
    assert all(title for title in topics.values())


def test_a_topic_carries_its_body_not_only_its_title() -> None:
    from app.services import help

    found = help.topic("patients")
    assert found["title"] == "Patients"
    assert "Search before you register" in found["body"]


def test_an_unknown_topic_is_none_rather_than_an_error() -> None:
    from app.services import help

    assert help.topic("not-a-screen") is None


def test_help_does_not_repeat_the_manual() -> None:
    """A screen's help is four short paragraphs; the manual is the manual."""

    for path in sorted(HELP.glob("*.md")):
        words = len(path.read_text(encoding="utf-8").split())
        assert words < 200, f"{path.name} is {words} words - that is a manual, not a help panel"


def test_help_speaks_in_the_same_voice_as_the_guides() -> None:
    """Second person, present tense, and it says what not to do."""

    text = " ".join((HELP / "patients.md").read_text(encoding="utf-8").split())
    assert " you " in text.lower()
    assert "before you register" in text.lower()


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


def test_the_endpoint_serves_a_topic(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/help/patients", headers=auth_headers())

    assert response.status_code == 200, response.text
    assert response.json()["view"] == "patients"


def test_the_endpoint_lists_the_topics(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        body = client.get("/api/v1/help", headers=auth_headers()).json()

    assert len(body["topics"]) >= 14


def test_an_unknown_topic_is_a_404(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        assert client.get("/api/v1/help/nope", headers=auth_headers()).status_code == 404


def test_help_needs_a_login_but_no_permission() -> None:
    """A person who cannot read the help for a screen they can open works blind."""

    from app.dependencies.permissions import AUTHENTICATED_ONLY_PATHS, PUBLIC_PATHS

    assert "/api/v1/help" in AUTHENTICATED_ONLY_PATHS
    assert "/api/v1/help" not in PUBLIC_PATHS


# -------------------------------------------------------------------- client
def test_the_panel_is_a_drawer_not_a_page() -> None:
    """Leaving a screen to read about the screen loses the patient you were registering."""

    source = (ROOT / "frontend" / "js" / "ui" / "help.js").read_text(encoding="utf-8")
    assert "aside" in source
    assert "hideHelp" in source


def test_the_client_escapes_before_it_formats() -> None:
    """Markdown-lite on unescaped text is an injection route."""

    source = (ROOT / "frontend" / "js" / "ui" / "help.js").read_text(encoding="utf-8")
    assert "escapeHtml(text)" in source
    assert ".replace(/`([^`]+)`/g" in source


def test_the_panel_is_hidden_when_printing() -> None:
    css = (ROOT / "frontend" / "css" / "ui.css").read_text(encoding="utf-8")
    assert "@media print { .help-panel" in css
