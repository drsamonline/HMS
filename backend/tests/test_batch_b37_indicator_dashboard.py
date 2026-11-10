"""Gate tests for build-plan batch B37: the indicator dashboard.

The spine declared the numbers; this shows them. Two properties matter and are
tested here: the dashboard names no indicator of its own, and a month without data
is drawn as a gap rather than as a zero.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "frontend" / "js" / "ui"


def test_the_sparkline_breaks_at_a_gap() -> None:
    """A missing month drawn as zero is a plunge that never happened."""

    source = (UI / "sparkline.js").read_text(encoding="utf-8")
    assert "segments.push(current)" in source
    assert "if (coord === null)" in source


def test_the_sparkline_refuses_to_draw_from_one_point() -> None:
    source = (UI / "sparkline.js").read_text(encoding="utf-8")
    assert "known.length < 2" in source
    assert "not enough months" in source


def test_the_sparkline_needs_no_charting_dependency() -> None:
    """One line per indicator does not justify a library on a LAN product."""

    source = (UI / "sparkline.js").read_text(encoding="utf-8")
    assert "<svg" in source
    assert "import" not in source.replace('import {', "SKIP") or "chart" not in source.lower()


def test_the_dashboard_names_no_indicator() -> None:
    """Adding an indicator is a backend change, which is the point of the spine."""

    source = (UI / "indicator-dashboard.js").read_text(encoding="utf-8")
    forbidden = ["opd_footfall", "bed_occupancy", "adverse_events", "certificates_issued"]
    found = [code for code in forbidden if code in source]
    assert not found, f"the dashboard hardcodes indicators: {found}"


def test_the_dashboard_renders_the_groups_the_server_sends() -> None:
    source = (UI / "indicator-dashboard.js").read_text(encoding="utf-8")
    assert "group_label" in source
    assert "groups.set(row.group" in source


def test_no_data_is_rendered_as_no_data() -> None:
    source = (UI / "indicator-dashboard.js").read_text(encoding="utf-8")
    assert "no data" in source
    assert "ind-value-empty" in source


def test_every_card_shows_its_definition() -> None:
    """A number nobody can check is a number nobody should trust."""

    source = (UI / "indicator-dashboard.js").read_text(encoding="utf-8")
    assert "row.numerator" in source
    assert "row.denominator" in source


def test_the_stylesheet_uses_tokens() -> None:
    css = (ROOT / "frontend" / "css" / "ui.css").read_text(encoding="utf-8")
    block = css[css.index(".ind-dashboard") :]
    literals = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", block)
    assert not literals, f"the dashboard carries literal colours: {literals}"


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


def test_the_series_returns_one_point_per_month(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get(
            "/api/v1/indicators/opd_footfall/series",
            headers=auth_headers(),
            params={"months": 6},
        )

    assert response.status_code == 200, response.text
    points = response.json()
    assert len(points) == 6
    assert all("value" in point and "available" in point for point in points)


def test_an_empty_series_reports_unavailable_months(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        points = client.get(
            "/api/v1/indicators/bed_occupancy/series",
            headers=auth_headers(),
            params={"months": 3},
        ).json()

    assert all(point["available"] is False for point in points)


def test_the_months_are_whole_calendar_months() -> None:
    """A rolling thirty days makes adjacent points share most of their data."""

    from datetime import UTC, datetime

    from app.services.indicators import month_periods

    periods = month_periods(datetime(2026, 11, 10, tzinfo=UTC), 3)
    assert len(periods) == 3
    for start, end in periods:
        assert start.day == 1
        assert end.day == 1
    assert periods[-1][0].month == 11


def test_the_series_needs_a_permission(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        assert client.get("/api/v1/indicators/opd_footfall/series").status_code == 401
