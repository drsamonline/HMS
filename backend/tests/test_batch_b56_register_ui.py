"""Gate tests for the statutory register screen and its alerts.

The register existed and only an API could read it, which meant nobody did. Two things
make it a register rather than a table: a screen somebody will actually open, and an
alert that appears on the home screen of the person who can renew the licence.

The rule that shapes the alert: it appears **only when there is something to do**. A
card that always says "nothing is expiring" is noise, and noise is what people learn to
ignore before it matters.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


# ---------------------------------------------------------------- the screen
def test_the_register_has_a_screen() -> None:
    assert (FRONTEND / "js" / "ui" / "institute-registrations.js").is_file()


def test_the_screen_reads_the_register_endpoint() -> None:
    source = (FRONTEND / "js" / "ui" / "institute-registrations.js").read_text(encoding="utf-8")
    assert "/api/v1/institute/registrations" in source


def test_the_screen_says_which_kinds_are_required() -> None:
    """Ten kinds, most of which a given clinic does not need."""

    source = (FRONTEND / "js" / "ui" / "institute-registrations.js").read_text(encoding="utf-8")
    assert "required_by_default" in source
    assert "reg-required" in source


def test_the_screen_explains_each_kind() -> None:
    """'What is this?' matters when the reader is a clinic manager, not a lawyer."""

    source = (FRONTEND / "js" / "ui" / "institute-registrations.js").read_text(encoding="utf-8")
    assert "What is this?" in source
    assert "escapeHtml(entry.note)" in source


def test_the_screen_escapes_what_it_renders() -> None:
    source = (FRONTEND / "js" / "ui" / "institute-registrations.js").read_text(encoding="utf-8")
    for field in ("entry.label", "entry.number", "entry.authority", "entry.note"):
        assert f"escapeHtml({field}" in source, f"{field} is rendered unescaped"


def test_a_registration_without_an_expiry_shows_a_dash() -> None:
    """An invented date would be worse than an empty cell."""

    source = (FRONTEND / "js" / "ui" / "institute-registrations.js").read_text(encoding="utf-8")
    assert 'entry.valid_until ? escapeHtml(entry.valid_until.slice(0, 10)) : "—"' in source


# ----------------------------------------------------------------- the alert
def test_the_superintendent_home_carries_the_alert_panel() -> None:
    from app.modules.homes import HOMES

    panels = HOMES["medical superintendent"].panels
    registration_panels = [panel for panel in panels if panel.kind == "registrations"]
    assert len(registration_panels) == 1


def test_the_alert_hides_when_there_is_nothing_to_say() -> None:
    """A card that always says 'nothing is expiring' teaches people to ignore it."""

    from app.modules.homes import HOMES

    panel = next(
        panel
        for panel in HOMES["medical superintendent"].panels
        if panel.kind == "registrations"
    )
    assert panel.hide_when_empty is True


def test_the_alert_points_at_the_screen_that_can_fix_it() -> None:
    from app.modules.homes import HOMES
    from app.modules.navigation import BY_VIEW

    panel = next(
        panel
        for panel in HOMES["medical superintendent"].panels
        if panel.kind == "registrations"
    )
    assert panel.view in BY_VIEW


# ------------------------------------------------------------------ runtime
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


def test_the_home_endpoint_serves_the_alert_with_its_items(isolated) -> None:
    """A fresh installation has recorded nothing, so the alert has plenty to say."""

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        body = client.get("/api/v1/home", headers=auth_headers()).json()

    panel = next((p for p in body["panels"] if p["kind"] == "registrations"), None)
    assert panel is not None, "the alert did not appear on a fresh install"
    assert panel["data"]["count"] >= 2
    assert "need attention" in panel["data"]["headline"]
    assert panel["data"]["items"]


def test_the_home_endpoint_omits_the_alert_once_everything_is_recorded(isolated) -> None:
    """When there is nothing to do, the card goes away entirely."""

    import asyncio
    from datetime import UTC, datetime, timedelta

    from app.db.session import get_session_factory
    from app.services import institute_registrations
    from tests._qa_harness import auth_headers, make_client

    future = datetime.now(UTC) + timedelta(days=365)

    with make_client() as client:
        factory = get_session_factory()

        async def _fill():
            async with factory() as db:
                for kind in ("clinical_establishment", "biomedical_waste"):
                    await institute_registrations.upsert(
                        db, kind=kind, number=f"X/{kind}", valid_until=future
                    )
                # Everything else marked as not applying to this establishment.
                from app.models.institute_registration import KIND_CODES

                for kind in KIND_CODES:
                    if kind in {"clinical_establishment", "biomedical_waste"}:
                        continue
                    await institute_registrations.upsert(
                        db, kind=kind, number="n/a", applies=False, valid_until=None
                    )
                await db.commit()

        asyncio.run(_fill())
        body = client.get("/api/v1/home", headers=auth_headers()).json()

    assert not [p for p in body["panels"] if p["kind"] == "registrations"], (
        "the alert is still showing with nothing to report"
    )
