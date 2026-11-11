"""Gate tests for build-plan batch B18: one navigation manifest.

Three things have to agree and, until this batch, two of them were hardcoded in
the client and could not be checked at all:

1. the manifest declares every sidebar view, with a module and a permission;
2. the server filters it by enabled modules and held permissions;
3. the static markup in ``index.html`` - the fallback for a failed request -
   matches the manifest exactly, so it cannot drift.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.core.permissions import CODES
from app.modules.navigation import BY_VIEW, NAV_ITEMS
from app.modules.registry import BY_CODE

ENTRY = Path(__file__).resolve().parents[2] / "frontend" / "index.html"


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch):
    """Start every test from a clean cache.

    The endpoint tests use the QA harness, which builds an in-memory database from
    whatever ``DATABASE_URL`` resolves to. A neighbouring test module that points
    the settings at a file database leaves that resolution cached, and these tests
    then read the wrong one - they pass alone and fail in company.
    """

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


# ------------------------------------------------------------- the manifest
def test_every_view_is_declared_once() -> None:
    views = [item.view for item in NAV_ITEMS]
    assert len(views) == len(set(views)), "duplicate view in the manifest"


def test_every_item_names_a_real_module() -> None:
    for item in NAV_ITEMS:
        assert item.module in BY_CODE, f"{item.view} names unknown module {item.module}"


def test_every_item_names_a_real_permission() -> None:
    for item in NAV_ITEMS:
        if item.permission is None:
            continue
        assert item.permission in CODES, (
            f"{item.view} requires {item.permission}, which the catalogue does not declare"
        )


def test_only_the_dashboard_needs_no_permission() -> None:
    """A screen with no permission is visible to everyone who can log in."""

    open_items = [item.view for item in NAV_ITEMS if item.permission is None]
    assert open_items == ["dashboard"], open_items


# --------------------------------------------------- the fallback cannot drift
def test_static_markup_matches_the_manifest() -> None:
    """The fallback list is the manifest's shadow; a mismatch fails the build."""

    html = ENTRY.read_text(encoding="utf-8")
    markup_views = re.findall(r'class="nav-item[^"]*"\s+data-app-view="([^"]+)"', html)
    # the pattern above assumes attribute order; fall back to a looser scan
    if not markup_views:
        markup_views = re.findall(r'data-app-view="([^"]+)"', html)

    assert sorted(markup_views) == sorted(BY_VIEW), (
        "index.html and the navigation manifest disagree.\n"
        f"  only in markup:   {sorted(set(markup_views) - set(BY_VIEW))}\n"
        f"  only in manifest: {sorted(set(BY_VIEW) - set(markup_views))}"
    )


def test_the_client_no_longer_keeps_its_own_list() -> None:
    """navigation.js must ask the server, not carry a second copy."""

    source = (ENTRY.parent / "js" / "navigation.js").read_text(encoding="utf-8")
    assert "/api/v1/navigation" in source
    for view in BY_VIEW:
        assert f'"{view}"' not in source, (
            f"navigation.js hardcodes the view {view!r}; the manifest is the source"
        )


# ------------------------------------------------------------ server filtering
def _headers() -> dict:
    from tests._qa_harness import auth_headers

    return auth_headers()


def test_the_endpoint_returns_the_whole_menu_for_an_administrator() -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        response = client.get("/api/v1/navigation", headers=_headers())
    assert response.status_code == 200, response.text
    returned = {item["view"] for item in response.json()}
    assert returned == set(BY_VIEW), f"missing: {sorted(set(BY_VIEW) - returned)}"


def test_the_endpoint_hides_a_module_this_hospital_does_not_have() -> None:
    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models.module_state import ModuleState
    from tests._qa_harness import make_client

    import asyncio

    with make_client() as client:
        headers = _headers()

        factory = get_session_factory()

        async def _disable() -> None:
            async with factory() as db:
                state = (
                    await db.execute(
                        select(ModuleState).where(ModuleState.module_code == "stock")
                    )
                ).scalar_one()
                state.is_enabled = False
                await db.commit()

        asyncio.run(_disable())

        response = client.get("/api/v1/navigation", headers=headers)

    assert response.status_code == 200, response.text
    views = {item["view"] for item in response.json()}
    assert "inventory" not in views
    assert "procurement" not in views
    assert "patients" in views, "core views must survive"


def test_the_endpoint_requires_a_login() -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        assert client.get("/api/v1/navigation").status_code == 401
