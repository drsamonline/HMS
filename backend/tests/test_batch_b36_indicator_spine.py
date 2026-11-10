"""Gate tests for build-plan batch B36: the indicator spine.

Every number a hospital reports is defined once, in words a clinician can argue with:
what is counted, what it is divided by, over what period, and which NABH element it
answers. The engine computes what the catalogue declares; nothing computes a figure
that is not declared.

The alternative - a dashboard query per number - is how two screens end up showing
two different occupancies for the same day.
"""

from __future__ import annotations

import pytest


# ------------------------------------------------------------------ catalogue
def test_every_indicator_declares_its_numerator_and_denominator() -> None:
    """A ratio whose denominator is not stated is a number nobody can check."""

    from app.core.indicators import INDICATORS

    for indicator in INDICATORS:
        assert indicator.numerator.strip(), f"{indicator.code} has no numerator"
        assert indicator.denominator.strip(), f"{indicator.code} has no denominator"


def test_every_indicator_names_a_unit_and_a_group() -> None:
    from app.core.indicators import GROUPS, INDICATORS

    groups = {code for code, _label in GROUPS}
    for indicator in INDICATORS:
        assert indicator.unit in {"count", "visits", "admissions", "certificates", "percent", "ratio"}
        assert indicator.group in groups, f"{indicator.code} is in no declared group"


def test_every_indicator_has_a_computer() -> None:
    """A declared indicator with no engine is a promise, not a number."""

    from app.core.indicators import INDICATORS
    from app.services.indicators import COMPUTERS

    missing = [indicator.code for indicator in INDICATORS if indicator.code not in COMPUTERS]
    assert not missing, f"declared but not computed: {missing}"


def test_no_computer_is_undeclared() -> None:
    """The other direction: a number computed but not described is a number nobody
    can argue with."""

    from app.core.indicators import BY_CODE
    from app.services.indicators import COMPUTERS

    extra = [code for code in COMPUTERS if code not in BY_CODE]
    assert not extra, f"computed but not declared: {extra}"


def test_every_indicator_names_the_standard_it_answers() -> None:
    """Not decoration: this is what an assessor asks to see."""

    from app.core.indicators import INDICATORS

    for indicator in INDICATORS:
        assert indicator.standard, f"{indicator.code} answers no stated standard"
        assert indicator.standard.startswith(("NABH", "NCH"))


def test_codes_are_unique() -> None:
    from app.core.indicators import INDICATORS

    codes = [indicator.code for indicator in INDICATORS]
    assert len(codes) == len(set(codes))


# ------------------------------------------------------------------- honesty
def test_an_empty_denominator_returns_none_not_zero() -> None:
    """'No admissions' and '0% of admissions' are different statements."""

    from app.services.indicators import _percent, _ratio

    assert _ratio(0, 0) is None
    assert _percent(0, 0) is None
    assert _ratio(3, 0) is None


def test_a_real_zero_is_still_zero() -> None:
    """None means nothing to divide by; a true zero must survive as a number."""

    from app.services.indicators import _percent, _ratio

    assert _ratio(0, 5) == 0
    assert _percent(0, 5) == 0


def test_the_engine_reports_availability_separately_from_the_value() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "indicators.py"
    ).read_text(encoding="utf-8")
    assert '"available": value is not None' in source


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


def test_the_endpoint_returns_every_indicator(isolated) -> None:
    from app.core.indicators import INDICATORS
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/indicators", headers=auth_headers())

    assert response.status_code == 200, response.text
    assert len(response.json()) == len(INDICATORS)
    for row in response.json():
        assert "numerator" in row and "denominator" in row


def test_an_empty_hospital_reports_nothing_available_rather_than_zeroes(isolated) -> None:
    """A fresh installation has no numbers, and must say so."""

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        rows = client.get("/api/v1/indicators", headers=auth_headers()).json()

    ratios = [row for row in rows if row["unit"] in {"percent", "ratio"}]
    assert all(row["value"] is None for row in ratios), (
        "a ratio with no denominator must be None, not 0"
    )
    assert all(row["available"] is False for row in ratios)


def test_the_catalogue_is_readable_without_computing(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/indicators/catalogue", headers=auth_headers())

    assert response.status_code == 200, response.text
    assert all("group_label" in row for row in response.json())


def test_an_unknown_indicator_is_a_404(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/indicators/nonsense", headers=auth_headers())

    assert response.status_code == 404, response.text


def test_a_malformed_date_is_refused(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get(
            "/api/v1/indicators",
            headers=auth_headers(),
            params={"start": "last tuesday"},
        )

    assert response.status_code == 422, response.text


def test_the_indicators_need_a_permission(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        assert client.get("/api/v1/indicators").status_code == 401
