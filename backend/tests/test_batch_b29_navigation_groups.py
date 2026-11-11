"""Gate tests for build-plan batch B29: navigation groups.

The sidebar was fourteen buttons in a column. That is not a menu - it is a list of
everything the software can do, in the order it happened to be built.

Six groups now, ordered the way a hospital works: the front desk opens patients
before anyone looks at a report, and administration is last because nobody opens it
twice a day.
"""

from __future__ import annotations

import pytest


def test_every_item_belongs_to_a_declared_group() -> None:
    from app.modules.navigation import NAV_GROUPS, NAV_ITEMS

    codes = {group.code for group in NAV_GROUPS}
    orphans = [item.view for item in NAV_ITEMS if item.group not in codes]
    assert not orphans, f"items in no declared group: {orphans}"


def test_group_order_is_unique_and_ascending() -> None:
    from app.modules.navigation import NAV_GROUPS

    orders = [group.order for group in NAV_GROUPS]
    assert len(orders) == len(set(orders)), "two groups share an order"
    assert orders == sorted(orders), "groups are declared out of order"


def test_no_group_is_empty() -> None:
    """A heading with nothing under it tells a user about a screen they cannot open."""

    from app.modules.navigation import NAV_GROUPS, NAV_ITEMS

    used = {item.group for item in NAV_ITEMS}
    empty = [group.code for group in NAV_GROUPS if group.code not in used]
    assert not empty, f"groups declared with no items: {empty}"


def test_the_sidebar_is_no_longer_one_flat_column() -> None:
    from app.modules.navigation import NAV_GROUPS, NAV_ITEMS

    assert len(NAV_GROUPS) >= 4, "fewer than four groups is still a flat list"
    assert len(NAV_ITEMS) > len(NAV_GROUPS)


def test_the_front_desk_group_comes_before_administration() -> None:
    """Order is how a hospital works, not the alphabet."""

    from app.modules.navigation import BY_GROUP

    assert BY_GROUP["front-desk"].order < BY_GROUP["administration"].order
    assert BY_GROUP["front-desk"].order < BY_GROUP["clinical"].order


def test_the_endpoint_carries_the_group_label_and_order() -> None:
    from app.api.v1.endpoints.navigation import NavItemRead

    fields = set(NavItemRead.model_fields)
    assert {"group", "group_label", "group_order"} <= fields


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


def test_an_administrator_sees_every_group(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/navigation", headers=auth_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    groups = {item["group"] for item in body}
    assert "front-desk" in groups
    assert "administration" in groups
    assert all(item["group_label"] for item in body)
    assert all(isinstance(item["group_order"], int) for item in body)


def test_the_client_groups_by_the_order_the_server_sent() -> None:
    """The order is the server's, not the client's.""" 

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "navigation.js"
    ).read_text(encoding="utf-8")
    assert "group_order" in source
    assert "a[1].order - b[1].order" in source
    assert "nav-group-title" in source


def test_the_client_removes_a_group_it_cannot_fill() -> None:
    """A heading with nothing under it is worse than no heading."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "navigation.js"
    ).read_text(encoding="utf-8")
    assert "if (moved > 0)" in source
