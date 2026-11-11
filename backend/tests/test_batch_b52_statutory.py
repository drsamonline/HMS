"""Gate tests for the statutory registrations batch.

The correction that prompted this: a practitioner's number comes from a State Council
in most states, not from NCH, so a field called "NCH registration number" assumed an
answer. And the institution's registrations - clinical establishment, bio-medical
waste - are different facts issued by different bodies, held once per premises rather
than once per doctor.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


# ------------------------------------------------------------------ practitioner
def test_the_practitioner_records_who_issued_the_number() -> None:
    """A State Council number is as valid as an NCH one, and more common."""

    from app.models.user import User

    assert "registration_number" in User.__table__.columns
    assert "registration_authority" in User.__table__.columns


def test_the_authority_is_optional() -> None:
    """An installation that has not filled it in must still work."""

    from app.models.user import User

    assert User.__table__.columns["registration_authority"].nullable is True


# ------------------------------------------------------------------ institute
def test_every_registration_kind_is_declared_once() -> None:
    from app.models.institute_registration import KIND_CODES, REGISTRATION_KINDS

    assert len(KIND_CODES) == len(set(KIND_CODES)) == len(REGISTRATION_KINDS)


def test_every_kind_says_who_issues_it() -> None:
    """A register that names a licence without naming the authority is half a register."""

    from app.models.institute_registration import REGISTRATION_KINDS

    for code, label, note in REGISTRATION_KINDS:
        assert label
        assert len(note) > 30, f"{code} does not say who issues it or when it applies"


def test_the_two_the_law_requires_of_a_private_practice_are_mandatory() -> None:
    """Clinical establishment and BMW apply to a single-doctor clinic."""

    from app.models.institute_registration import MANDATORY_BY_DEFAULT

    assert set(MANDATORY_BY_DEFAULT) == {"clinical_establishment", "biomedical_waste"}


def test_nabh_and_qci_are_not_mandatory() -> None:
    """A clinic may operate without accreditation, and this software does not require it."""

    from app.models.institute_registration import MANDATORY_BY_DEFAULT

    assert "nabh" not in MANDATORY_BY_DEFAULT
    assert "qci" not in MANDATORY_BY_DEFAULT


def test_the_optional_kinds_are_marked_as_conditional() -> None:
    """A lift licence is not required of a clinic with no lift."""

    from app.models.institute_registration import REGISTRATION_KINDS

    notes = {code: note for code, _label, note in REGISTRATION_KINDS}
    for conditional in ("lift_licence", "generator_consent", "fire_safety"):
        assert "where" in notes[conditional].lower()


# ------------------------------------------------------------------ readiness
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


def test_a_fresh_installation_is_told_what_it_has_not_recorded(isolated) -> None:
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

    at_risk = {entry["kind"] for entry in report["at_risk"]}
    assert "clinical_establishment" in at_risk
    assert "biomedical_waste" in at_risk
    assert "nabh" not in at_risk, "accreditation is not a gap"


def test_an_expired_registration_is_reported_as_expired(isolated) -> None:
    import asyncio

    from app.db.session import get_session_factory
    from app.services import institute_registrations
    from tests._qa_harness import make_client

    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await institute_registrations.upsert(
                    db,
                    kind="biomedical_waste",
                    number="BMW/2024/1234",
                    authority="State Pollution Control Board",
                    valid_until=datetime.now(UTC) - timedelta(days=10),
                )
                await db.commit()
                return await institute_registrations.readiness(db)

        report = asyncio.run(_go())

    entry = next(item for item in report["registrations"] if item["kind"] == "biomedical_waste")
    assert entry["state"] == "expired"


def test_a_registration_expiring_soon_is_a_warning_not_a_failure(isolated) -> None:
    import asyncio

    from app.db.session import get_session_factory
    from app.services import institute_registrations
    from tests._qa_harness import make_client

    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await institute_registrations.upsert(
                    db,
                    kind="clinical_establishment",
                    number="CEA/2026/99",
                    valid_until=datetime.now(UTC) + timedelta(days=20),
                )
                await db.commit()
                return await institute_registrations.readiness(db)

        report = asyncio.run(_go())

    entry = next(
        item for item in report["registrations"] if item["kind"] == "clinical_establishment"
    )
    assert entry["state"] == "expiring"


def test_a_registration_with_no_expiry_is_not_expired(isolated) -> None:
    """Some registrations are issued without one; an invented date is worse than none."""

    import asyncio

    from app.db.session import get_session_factory
    from app.services import institute_registrations
    from tests._qa_harness import make_client

    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await institute_registrations.upsert(
                    db, kind="shop_establishment", number="SE/2026/1", valid_until=None
                )
                await db.commit()
                return await institute_registrations.readiness(db)

        report = asyncio.run(_go())

    entry = next(item for item in report["registrations"] if item["kind"] == "shop_establishment")
    assert entry["state"] == "current"


def test_an_unknown_kind_is_refused(isolated) -> None:
    import asyncio

    from app.core.exceptions import BusinessRuleException
    from app.db.session import get_session_factory
    from app.services import institute_registrations
    from tests._qa_harness import make_client

    with make_client() as client:
        factory = get_session_factory()

        async def _go():
            async with factory() as db:
                await institute_registrations.upsert(db, kind="not_a_licence", number="X")

        with pytest.raises(BusinessRuleException, match="not a registration"):
            asyncio.run(_go())


def test_the_report_refuses_to_decide_what_the_law_requires(isolated) -> None:
    """That depends on the state and the premises, and the software says so."""

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

    assert "depends on the state" in report["note"]


# ------------------------------------------------------------------ editions
def test_nabh_is_available_from_the_hospital_edition_upward() -> None:
    """A hospital that is not pursuing accreditation turns it off; it is not blocked."""

    from app.core.editions import CLINIC, ENTERPRISE, HOSPITAL, PERSONAL

    assert "nabh" not in PERSONAL.modules
    assert "nabh" not in CLINIC.modules
    assert "nabh" in HOSPITAL.modules
    assert "nabh" in ENTERPRISE.modules


def test_qci_is_an_institute_feature_not_a_clinic_one() -> None:
    from app.core.editions import CLINIC, ENTERPRISE, HOSPITAL, PERSONAL

    for edition in (PERSONAL, CLINIC, HOSPITAL):
        assert "qci_accreditation" not in edition.features
    assert "qci_accreditation" in ENTERPRISE.features


# ------------------------------------------------------------------ endpoint
def test_the_endpoint_serves_the_register(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get("/api/v1/institute/registrations", headers=auth_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["registrations"]) == 10
    assert body["at_risk"]


def test_a_registration_can_be_recorded_through_the_api(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.put(
            "/api/v1/institute/registrations/biomedical_waste",
            headers=auth_headers(),
            json={"number": "BMW/2026/77", "authority": "SPCB", "valid_until": "2027-03-31T00:00:00Z"},
        )

    assert response.status_code == 200, response.text
    entry = next(
        item for item in response.json()["registrations"] if item["kind"] == "biomedical_waste"
    )
    assert entry["state"] == "current"
    assert entry["number"] == "BMW/2026/77"
