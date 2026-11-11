"""Gate tests for the discharge outcome and the four indicators it unlocked.

The first PSQ.3 assessment said length of stay could not be computed because there
was no discharge timestamp anywhere. That was wrong: a separate Discharge table has
one. The data was there; the assessment had looked in one place.

What genuinely was missing is the outcome - whether the patient went home, died,
left against advice or was transferred. These tests hold the rule that makes the
outcome honest: an episode nobody classified has an unknown outcome, not a good one.
"""

from __future__ import annotations

import pytest


def test_the_outcome_is_separate_from_the_status() -> None:
    """Status says the record is valid; outcome says what happened to the patient."""

    from app.models.discharge import Discharge

    assert "discharge_status" in Discharge.__table__.columns
    assert "discharge_outcome" in Discharge.__table__.columns


def test_the_outcome_is_nullable() -> None:
    """Existing rows stay null rather than being assumed routine."""

    from app.models.discharge import Discharge

    assert Discharge.__table__.columns["discharge_outcome"].nullable is True


def test_the_four_outcomes_are_declared() -> None:
    from app.schemas.discharge import DischargeOutcome

    assert set(DischargeOutcome.__args__) == {
        "routine",
        "expired",
        "against_advice",
        "transferred",
    }


def test_the_mortality_denominator_counts_only_classified_episodes() -> None:
    """Otherwise mortality falls as record-keeping gets worse."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "indicators.py"
    ).read_text(encoding="utf-8")
    assert "Discharge.discharge_outcome.is_not(None)" in source
    assert "nobody classified has an unknown outcome" in source.lower() or "Nobody classified" in source


def test_length_of_stay_reads_the_discharge_table() -> None:
    """The timestamp was always there; the first assessment looked elsewhere."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "indicators.py"
    ).read_text(encoding="utf-8")
    assert "Discharge.discharge_datetime" in source
    assert "async def average_length_of_stay" in source


def test_the_four_new_indicators_are_declared_and_computed() -> None:
    from app.core.indicators import BY_CODE
    from app.services.indicators import COMPUTERS

    for code in (
        "average_length_of_stay",
        "readmissions_30d",
        "inpatient_mortality",
        "discharge_against_advice",
    ):
        assert code in BY_CODE, f"{code} is not declared"
        assert code in COMPUTERS, f"{code} is not computed"


def test_every_declared_indicator_still_has_a_computer() -> None:
    from app.core.indicators import INDICATORS
    from app.services.indicators import COMPUTERS

    assert {indicator.code for indicator in INDICATORS} == set(COMPUTERS)


def test_an_empty_denominator_is_still_none() -> None:
    """The rule survives the new indicators."""

    from app.services.indicators import _percent

    assert _percent(0, 0) is None


# ---------------------------------------------------------------- the document
def test_the_document_records_the_correction() -> None:
    """A gap analysis that named one table and not its siblings reported a gap
    that was not there. That is worth recording rather than tidying away."""

    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "docs" / "NABH-PSQ3.md").read_text(
        encoding="utf-8"
    )
    assert "That was wrong" in text
    assert "discharge_outcome" in text


def test_the_coverage_report_counts_the_new_families() -> None:
    from app.core.psq3 import coverage

    report = coverage()
    assert report["families_with_any_data"] >= 6
    assert "average_length_of_stay" in report["indicators_live"]
    assert "inpatient_mortality" in report["indicators_live"]


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


def test_the_endpoint_serves_thirteen_indicators(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        rows = client.get("/api/v1/indicators", headers=auth_headers()).json()

    assert len(rows) == 13
    outcomes = [row for row in rows if row["group"] == "outcomes"]
    assert len(outcomes) == 3
