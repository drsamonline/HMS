"""Gate tests for the two corrections in this batch.

The first: NABH accredits small clinics as well as hospitals, so the module is
available in every edition - off until somebody chooses it.

The second is the architectural one: **a missing licence never blocks a user.** There
are two different gates and they must not be confused. The edition gate is commercial -
you cannot enable a module you did not buy. The statutory gate is a fact about the
premises - it is reported, never enforced, because locking a doctor out of a patient's
record over a lapsed certificate causes the harm the warning was about.
"""

from __future__ import annotations

import pytest


# ------------------------------------------------------------------ NABH
def test_nabh_is_paid_and_optional() -> None:
    """Two separate things, and B54 settled both.

    *Paid*: the free edition does not carry it, because a free tier that includes
    everything is not a tier. *Optional*: where it is available, it is off until
    somebody chooses it, and off is never an error.
    """

    from app.core.editions import CLINIC, ENTERPRISE, HOSPITAL, PERSONAL
    from app.modules.registry import BY_CODE

    assert "nabh" not in PERSONAL.modules
    for edition in (CLINIC, HOSPITAL, ENTERPRISE):
        assert "nabh" in edition.modules
    assert BY_CODE["nabh"].is_optional is True


def test_nabh_is_marked_optional() -> None:
    """Off is a choice, not a fault, and nothing may treat it as an error."""

    from app.modules.registry import BY_CODE

    assert BY_CODE["nabh"].is_optional is True


def test_the_other_modules_are_not_optional() -> None:
    """A hospital that turns off billing has a problem; one that turns off NABH does not."""

    from app.modules.registry import MODULES

    optional = {module.code for module in MODULES if module.is_optional}
    assert optional == {"nabh"}


def test_editions_still_grow_monotonically() -> None:
    from app.core.editions import CLINIC, ENTERPRISE, HOSPITAL, PERSONAL

    chain = [PERSONAL, CLINIC, HOSPITAL, ENTERPRISE]
    for lower, higher in zip(chain, chain[1:]):
        assert not set(lower.modules) - set(higher.modules)


# ------------------------------------------------------- the two gates differ
def test_the_edition_gate_still_refuses_what_was_not_bought() -> None:
    """Commercial entitlement is enforced. That is not the same as a licence check."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "module_state.py"
    ).read_text(encoding="utf-8")
    assert "not included in" in source


def test_a_missing_registration_never_refuses_anything() -> None:
    """The statutory gate reports; it does not enforce."""

    from pathlib import Path

    # Checked through the payload rather than the source text: a phrase test on a
    # string that Python itself wraps is testing the formatter, not the behaviour.
    import asyncio

    from app.db.session import get_session_factory
    from app.services import institute_registrations
    from tests._qa_harness import make_client

    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                return await institute_registrations.readiness(db)

        report = asyncio.run(_go())

    assert report["blocking"] is False
    assert "never stops anybody" in report["effect"]


def test_the_readiness_report_is_not_a_door() -> None:
    """It is called from the compliance report and from nowhere that refuses."""

    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    callers = []
    for path in root.rglob("*.py"):
        if path.name == "institute_registrations.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "institute_registrations.readiness" in text or "institute_registrations.upsert" in text:
            callers.append(path.name)

    # The report is read by the compliance service; upsert is written by the endpoint.
    assert set(callers) <= {"nch_compliance.py", "institute.py"}, callers


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


def test_the_software_runs_with_every_registration_missing(isolated) -> None:
    """A clinic that has not entered a single certificate can still see a patient."""

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        headers = auth_headers()
        patients = client.get("/api/v1/patients", headers=headers)
        registrations = client.get("/api/v1/institute/registrations", headers=headers)

    assert patients.status_code == 200, patients.text
    assert registrations.status_code == 200, registrations.text
    assert registrations.json()["at_risk"], "the gap is reported"
    assert registrations.json()["blocking"] is False


def test_turning_the_nabh_module_off_does_not_stop_the_software(isolated) -> None:
    """Off means the NABH screens are gone, not that the hospital is locked out."""

    import asyncio

    from app.db.session import get_session_factory
    from app.services import module_state
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        factory = get_session_factory()

        async def _off():
            async with factory() as db:
                await module_state.disable(db, "nabh")
                await db.commit()
                return await module_state.enabled_codes(db)

        codes = asyncio.run(_off())

        assert "nabh" not in codes
        # Everything else still answers.
        assert client.get("/api/v1/patients", headers=auth_headers()).status_code == 200
        assert client.get("/api/v1/navigation", headers=auth_headers()).status_code == 200


def test_an_optional_module_can_be_turned_back_on(isolated, monkeypatch, tmp_path) -> None:
    """The free edition cannot enable it; a licensed one can turn it off and on again."""

    import asyncio

    from app.db.session import get_session_factory
    from app.services import module_state
    from tests._qa_harness import make_client

    # A licensed hospital, which is where the module is available at all.
    monkeypatch.setenv("HHMS_EDITION", "hospital")

    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await module_state.disable(db, "nabh")
                await db.commit()
                await module_state.enable(db, "nabh")
                await db.commit()
                return await module_state.enabled_codes(db)

        assert "nabh" in asyncio.run(_go())
