"""Gate tests for build-plan batch B23: the steps that create data.

Four of the ten steps write rows rather than settings. Two properties matter and
are tested here: each step is idempotent, because a wizard is a thing people click
twice; and no step can touch data it has no business touching.
"""

from __future__ import annotations

import pytest


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


def _reset() -> None:
    """Empty the tables these steps write.

    ``make_client`` reuses one in-memory database within a module run, so a row
    created by one test is still there for the next. Every test here starts from
    the state a real wizard would: nothing created yet.
    """

    import asyncio

    from sqlalchemy import delete

    import app.models as models
    from app.db.session import get_session_factory
    from app.models.setup_state import SetupState

    factory = get_session_factory()

    async def _go():
        async with factory() as db:
            for model in (models.Bed, models.Department, models.NumberSequence, SetupState):
                await db.execute(delete(model))
            await db.commit()

    asyncio.run(_go())


def _setup_headers() -> dict:
    from app.auth.jwt import create_access_token

    token = create_access_token(subject="setup", additional_claims={"scope": "setup"})
    return {"Authorization": f"Bearer {token}"}


def _step(client, step: str, values: dict) -> dict:
    return client.post(
        f"/api/v1/setup/steps/{step}", headers=_setup_headers(), json={"values": values}
    )


def _count(model_name: str) -> int:
    import asyncio

    from sqlalchemy import func, select

    from app.db.session import get_session_factory
    import app.models as models

    model = getattr(models, model_name)
    factory = get_session_factory()

    async def _go():
        async with factory() as db:
            return (await db.execute(select(func.count()).select_from(model))).scalar_one()

    return asyncio.run(_go())


# --------------------------------------------------------------------- wards
def test_wards_become_beds(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "wards", {"wards": [{"name": "General", "beds": 4}]})
        beds = _count("Bed")  # inside the block: the database is in-memory

    assert response.status_code == 200, response.text
    assert response.json()["beds_created"] == 4
    assert beds == 4


def test_wards_are_idempotent(isolated) -> None:
    """A second click must not create a second ward with the same name."""

    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "wards", {"wards": [{"name": "General", "beds": 4}]})
        second = _step(client, "wards", {"wards": [{"name": "General", "beds": 4}]})
        beds = _count("Bed")

    assert second.status_code == 200, second.text
    assert second.json()["beds_created"] == 0, "the second click created beds again"
    assert beds == 4


def test_a_ward_needs_a_name(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "wards", {"wards": [{"name": "  ", "beds": 2}]})

    assert response.status_code == 422, response.text
    assert "needs a name" in response.json()["error"]["message"]


# --------------------------------------------------------------- departments
def test_departments_are_created_once(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        first = _step(client, "departments", {"departments": ["OPD", "Pharmacy"]})
        second = _step(client, "departments", {"departments": ["OPD", "Pharmacy"]})
        departments = _count("Department")

    assert first.status_code == 200, first.text
    assert first.json()["departments_created"] == ["OPD", "Pharmacy"]
    assert second.json()["departments_created"] == []
    assert departments == 2


# ------------------------------------------------------------------ numbering
def test_numbering_creates_every_required_sequence(isolated) -> None:
    from app.services.setup_steps import REQUIRED_SEQUENCES
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(client, "numbering", {})
        sequences = _count("NumberSequence")

    assert response.status_code == 200, response.text
    assert set(response.json()["sequences_created"]) == {
        name for name, _prefix, _padding in REQUIRED_SEQUENCES
    }
    assert sequences == len(REQUIRED_SEQUENCES)


def test_numbering_does_not_reset_an_existing_counter(isolated) -> None:
    """An installation that has been issuing numbers must not be reset by a wizard."""

    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models.number_sequence import NumberSequence
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "numbering", {})

        factory = get_session_factory()

        async def _bump():
            async with factory() as db:
                row = (
                    await db.execute(
                        select(NumberSequence).where(
                            NumberSequence.sequence_name == "patient_number"
                        )
                    )
                ).scalar_one()
                row.current_value = 137
                await db.commit()

        asyncio.run(_bump())

        second = _step(client, "numbering", {})
        assert second.json()["sequences_created"] == []

        async def _read():
            async with factory() as db:
                row = (
                    await db.execute(
                        select(NumberSequence).where(
                            NumberSequence.sequence_name == "patient_number"
                        )
                    )
                ).scalar_one()
                return row.current_value

        assert asyncio.run(_read()) == 137, "the wizard reset a live counter"


def test_numbering_accepts_a_prefix_override(isolated) -> None:
    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models.number_sequence import NumberSequence
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        response = _step(
            client, "numbering", {"prefixes": {"patient_number": "HH-"}}
        )
        assert response.status_code == 200, response.text

        factory = get_session_factory()

        async def _read():
            async with factory() as db:
                row = (
                    await db.execute(
                        select(NumberSequence).where(
                            NumberSequence.sequence_name == "patient_number"
                        )
                    )
                ).scalar_one()
                return row.prefix

        assert asyncio.run(_read()) == "HH-"


# ---------------------------------------------------------------------- money
def test_money_sets_only_the_money_prefixes(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "numbering", {})
        ok = _step(client, "money", {"prefixes": {"invoice_number": "BILL-"}})
        refused = _step(client, "money", {"prefixes": {"patient_number": "X-"}})

    assert ok.status_code == 200, ok.text
    assert ok.json()["prefixes_updated"] == ["invoice_number"]
    assert refused.status_code == 422, refused.text
    assert "money step sets only" in refused.json()["error"]["message"]


def test_each_step_is_recorded_as_done(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        _reset()
        _step(client, "departments", {"departments": ["OPD"]})
        status = client.get("/api/v1/setup/status").json()

    assert "departments" in status["completed_steps"]
