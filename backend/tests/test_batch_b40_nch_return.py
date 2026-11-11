"""Gate tests for build-plan batch B40: the NCH monthly return and QCI honesty.

The NCH Code of Ethics makes four things software-visible, and a hospital has to be
able to produce them for a period. A return is something that gets filed; filing four
figures from four screens is how one of them ends up from the wrong month.

QCI asks a different set of questions, and HHMS holds almost none of that data. The
section is present and marked rather than left out, because a section that is missing
looks like a section that passed.
"""

from __future__ import annotations

import pytest


def test_the_return_carries_every_nch_duty() -> None:
    from app.services.compliance_return import NCH_RETURN

    codes = {code for code, _label, _standard, _indicator in NCH_RETURN}
    assert codes == {
        "registration_number",
        "reason_recorded",
        "certificates_issued",
        "adverse_events_reported",
    }


def test_every_duty_names_its_regulation() -> None:
    """A return line that does not cite the rule is a number without a reason."""

    from app.services.compliance_return import NCH_RETURN

    for _code, _label, standard, _indicator in NCH_RETURN:
        assert standard.startswith("NCH Code of Ethics")


def test_every_duty_with_an_indicator_names_one_that_exists() -> None:
    from app.core.indicators import BY_CODE
    from app.services.compliance_return import NCH_RETURN

    unknown = [
        indicator
        for _code, _label, _standard, indicator in NCH_RETURN
        if indicator is not None and indicator not in BY_CODE
    ]
    assert not unknown, f"the return names indicators that do not exist: {unknown}"


def test_every_qci_gap_says_why() -> None:
    """'Not available' without a reason is a shrug, not a gap analysis."""

    from app.services.compliance_return import QCI_GAPS

    assert QCI_GAPS, "the QCI section must not be empty"
    for _code, _name, reason in QCI_GAPS:
        assert reason and len(reason) > 20, "a gap with no explanation"


def test_the_return_is_marked_unsupported_rather_than_silent() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "compliance_return.py"
    ).read_text(encoding="utf-8")
    assert '"supported": False' in source


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


def test_the_endpoint_returns_the_document(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/indicators/nch-return", headers=auth_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "NCH monthly return"
    assert len(body["duties"]) == 4
    assert body["qci"]["supported"] is False
    assert body["qci"]["gaps"]


def test_an_empty_period_reports_unavailable_rather_than_zero(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        body = client.get(
            "/api/v1/indicators/nch-return", headers=auth_headers()
        ).json()

    # A count of zero is a true zero: no certificates issued is a fact, not a gap.
    # A ratio with nothing to divide by is the gap, and must not read as zero.
    ratios = [
        duty
        for duty in body["duties"]
        if duty["unit"] in {"percent", "ratio"}
    ]
    assert ratios, "the return should carry at least one ratio"
    assert all(duty["available"] is False for duty in ratios)


def test_the_endpoint_needs_a_permission(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        assert client.get("/api/v1/indicators/nch-return").status_code == 401


# -------------------------------------------------------------------- document
def test_the_return_prints_from_the_same_markup_it_previews() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "ui" / "compliance-return.js"
    ).read_text(encoding="utf-8")
    assert 'class="print-document"' in source
    assert "window.print()" in source
    assert source.count("print-document") == 1


def test_the_qci_section_is_rendered_not_omitted() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "ui" / "compliance-return.js"
    ).read_text(encoding="utf-8")
    assert "QCI measures" in source
    assert "data.qci.gaps" in source
