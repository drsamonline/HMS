"""Gate tests for build-plan batch B44: editions, and the licence that follows them.

A tier is a set of modules plus the licence that governs it. Two properties are worth
testing hard:

* the free edition is free to use, not free to copy - which is what makes a free tier
  compatible with a proprietary codebase;
* the tier is enforced on the server, because the wizard is one of three ways to
  switch a module on and the other two are an API call and a crafted request.
"""

from __future__ import annotations

import pytest


# ------------------------------------------------------------------ catalogue
def test_every_edition_includes_core() -> None:
    """A tier without the clinical core is not a product."""

    from app.core.editions import EDITIONS

    for edition in EDITIONS.values():
        assert "core" in edition.modules, f"{edition.code} has no core"


def test_every_edition_names_a_licence_and_a_summary() -> None:
    from app.core.editions import EDITIONS

    for edition in EDITIONS.values():
        assert edition.licence
        assert edition.summary
        assert len(edition.summary) < 120, "a summary a salesperson cannot repeat is not a summary"


def test_every_module_an_edition_names_exists() -> None:
    from app.core.editions import EDITIONS
    from app.modules.registry import BY_CODE

    unknown = [
        f"{edition.code}: {code}"
        for edition in EDITIONS.values()
        for code in edition.modules
        if code not in BY_CODE
    ]
    assert not unknown, f"editions name modules that do not exist: {unknown}"


def test_the_personal_edition_is_opd_only() -> None:
    """Registration, consultation, dispensing and billing. Nothing inpatient."""

    from app.core.editions import PERSONAL

    assert "core" in PERSONAL.modules
    assert "pharmacy" in PERSONAL.modules
    assert "billing" in PERSONAL.modules
    assert "ipd" not in PERSONAL.modules
    assert "nabh" not in PERSONAL.modules
    assert "laboratory" not in PERSONAL.modules


def test_the_personal_edition_prints_the_whole_case_and_the_bills() -> None:
    """The request was specific about this: print support is what makes it usable."""

    from app.core.editions import PERSONAL

    assert "print_case_bundle" in PERSONAL.features
    assert "print_bills" in PERSONAL.features


def test_compliance_reporting_starts_at_the_hospital_edition() -> None:
    """A personal practice has no NABH assessment to prepare for.

    B52 moved NABH from enterprise-only to hospital-and-above, because a hospital that
    is not pursuing accreditation should be able to turn the module off rather than be
    unable to have it at all.
    """

    from app.core.editions import EDITIONS

    with_nabh = sorted(code for code, edition in EDITIONS.items() if "nabh" in edition.modules)
    assert with_nabh == ["enterprise", "hospital"]


def test_editions_grow_monotonically() -> None:
    """A more expensive tier must not lose a module a cheaper one had."""

    from app.core.editions import CLINIC, ENTERPRISE, HOSPITAL, PERSONAL

    chain = [PERSONAL, CLINIC, HOSPITAL, ENTERPRISE]
    for lower, higher in zip(chain, chain[1:]):
        missing = set(lower.modules) - set(higher.modules)
        assert not missing, f"{higher.code} is missing {missing} that {lower.code} has"


def test_the_free_licence_is_noncommercial_and_not_a_grant_to_copy() -> None:
    from app.core.editions import PERSONAL

    assert "Noncommercial" in PERSONAL.licence
    # The distinction the whole tier rests on: free to use, not free to redistribute.


def test_an_unknown_edition_falls_back_rather_than_failing() -> None:
    """A mistyped environment variable should give a smaller product, not no server."""

    from app.core.editions import DEFAULT_EDITION, edition_for

    assert edition_for("nonsense").code == DEFAULT_EDITION
    assert edition_for(None).code == DEFAULT_EDITION
    assert edition_for("").code == DEFAULT_EDITION


def test_the_default_is_the_free_edition() -> None:
    """A hospital that has paid for more must say so, not get it by omission."""

    from app.core.editions import DEFAULT_EDITION

    assert DEFAULT_EDITION == "personal"


# ---------------------------------------------------------------- enforcement
@pytest.fixture()
def isolated(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("HHMS_APPLICATION_ROOT", raising=False)
    monkeypatch.delenv("HHMS_EDITION", raising=False)

    from app.config import settings as settings_module
    from app.db import session as session_module

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()
    yield
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def test_the_personal_edition_refuses_an_inpatient_module(isolated) -> None:
    """Enforced on the server, not only in the wizard."""

    import asyncio

    from app.core.exceptions import BusinessRuleException
    from app.db.session import get_session_factory
    from app.services import module_state
    from tests._qa_harness import make_client

    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                return await module_state.enable(db, "ipd")

        with pytest.raises(BusinessRuleException, match="not included"):
            asyncio.run(_go())


def test_the_personal_edition_allows_its_own_modules(isolated) -> None:
    import asyncio

    from app.db.session import get_session_factory
    from app.services import module_state
    from tests._qa_harness import make_client

    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                # The harness enables every module, so the assertion is that the
                # edition permitted it rather than that it changed anything.
                await module_state.enable(db, "pharmacy")
                return await module_state.enabled_codes(db)

        assert "pharmacy" in asyncio.run(_go())


def test_the_endpoint_names_what_is_not_included(isolated) -> None:
    """An upgrade conversation should start from the same facts on both sides."""

    from tests._qa_harness import make_client

    with make_client() as client:
        response = client.get("/api/v1/edition")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["code"] == "personal"
    assert "ipd" in [module["code"] for module in body["not_included"]]
    assert body["upgrades"]


def test_the_edition_endpoint_needs_no_login() -> None:
    """It is a licence statement, not hospital data."""

    from app.dependencies.permissions import PUBLIC_PATHS

    assert "/api/v1/edition" in PUBLIC_PATHS
