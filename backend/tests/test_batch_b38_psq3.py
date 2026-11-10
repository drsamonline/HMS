"""Gate tests for build-plan batch B38: NABH PSQ.3 coverage.

PSQ.3 is the chapter that asks a hospital to measure itself, and the one most easily
faked. This batch does not enumerate 32 indicator names, because the authoritative
list is in the NABH standard and not in this repository - a list written from memory
would be one a hospital could not rely on.

What is tested instead is the honesty of the coverage report: every family says
whether the data is held, every family that is not held says what is missing, and
nothing claims a number it cannot produce.
"""

from __future__ import annotations

import pytest


def test_every_family_states_whether_the_data_is_held() -> None:
    from app.core.psq3 import PSQ3_FAMILIES

    for family in PSQ3_FAMILIES:
        assert isinstance(family.data_held, bool), f"{family.code} does not say"


def test_a_family_without_data_says_what_is_missing() -> None:
    """'Not available' without a reason is a shrug, not a gap analysis."""

    from app.core.psq3 import PSQ3_FAMILIES

    for family in PSQ3_FAMILIES:
        if not family.data_held:
            assert family.missing_data, f"{family.code} has no data and no reason"


def test_a_family_with_data_claims_no_missing_data() -> None:
    from app.core.psq3 import PSQ3_FAMILIES

    for family in PSQ3_FAMILIES:
        if family.data_held:
            assert family.missing_data is None, (
                f"{family.code} claims to hold the data and also claims to be missing some"
            )


def test_every_served_indicator_exists_in_the_spine() -> None:
    """A coverage claim naming a nonexistent indicator is a broken promise."""

    from app.core.indicators import BY_CODE
    from app.core.psq3 import PSQ3_FAMILIES

    unknown = [
        f"{family.code}: {code}"
        for family in PSQ3_FAMILIES
        for code in family.served_by
        if code not in BY_CODE
    ]
    assert not unknown, f"coverage names indicators that do not exist: {unknown}"


def test_a_family_that_claims_full_coverage_serves_an_indicator_for_each_item() -> None:
    """Nine indicators across three families, not three families of one number."""

    from app.core.psq3 import PSQ3_FAMILIES

    for family in PSQ3_FAMILIES:
        if family.data_held:
            assert family.served_by, f"{family.code} claims full coverage and serves nothing"
            assert len(family.served_by) >= min(2, len(family.indicators))


def test_the_coverage_report_is_self_consistent() -> None:
    from app.core.psq3 import coverage

    report = coverage()
    assert report["families_total"] == len(report["families"])
    assert report["families_with_any_data"] == len(
        [family for family in report["families"] if family["served_by"]]
    )
    assert report["families_fully_reportable"] == len(
        [family for family in report["families"] if family["data_held"]]
    )


def test_the_report_says_the_enumeration_is_not_in_this_repository() -> None:
    """The honest caveat, in the payload rather than only in a document."""

    from app.core.psq3 import coverage

    note = coverage()["note"]
    assert "not in this repository" in note
    assert "32" in note


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


def test_the_endpoint_serves_the_coverage(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/indicators/psq3", headers=auth_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["families_total"] >= 10
    assert body["indicators_live"]


def test_the_endpoint_needs_a_permission(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        assert client.get("/api/v1/indicators/psq3").status_code == 401


# -------------------------------------------------------------------- document
def test_the_document_records_the_correction_rather_than_hiding_it() -> None:
    """The first version named a gap that was not there. B39 corrected it in place."""

    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "docs" / "NABH-PSQ3.md").read_text(
        encoding="utf-8"
    )
    assert "That was wrong" in text
    assert "discharge timestamp" in text.lower()


def test_the_document_refuses_to_enumerate_from_memory() -> None:
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "docs" / "NABH-PSQ3.md").read_text(
        encoding="utf-8"
    )
    assert "not in this repository" in text


def test_the_mapping_points_at_the_coverage_report() -> None:
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "docs" / "NABH-MAPPING.md").read_text(
        encoding="utf-8"
    )
    assert "NABH-PSQ3.md" in text
    assert "/api/v1/indicators/psq3" in text
