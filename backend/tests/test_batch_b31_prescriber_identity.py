"""Gate tests for build-plan batch B31: the prescriber on the prescription.

NCH Code of Ethics 7(2) requires the prescriber's registration number on every
prescription, and failing to display it is professional misconduct. The number was
stored on the practitioner since B33 and never reached the paper, because the client
was never sent it.

This closes the gap between "stored" and "printed", which is the whole difference
between a field and a compliance claim.
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


def test_the_read_model_carries_the_prescriber_and_their_number() -> None:
    from app.schemas.prescription import PrescriptionRead

    fields = set(PrescriptionRead.model_fields)
    assert {"prescriber_name", "prescriber_registration"} <= fields


def test_the_identity_lookup_is_one_query_for_many_prescribers() -> None:
    """A list of prescriptions must not become one query per row."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "prescription.py"
    ).read_text(encoding="utf-8")
    assert "async def prescriber_identities" in source
    assert "User.id.in_(user_ids)" in source


def test_an_unknown_prescriber_yields_none_rather_than_an_empty_string() -> None:
    """The print template decides whether to show the line; it needs the difference."""

    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "prescription.py"
    ).read_text(encoding="utf-8")
    assert "return {}" in source


def _clear_prescriptions() -> None:
    """Start from no prescriptions.

    The harness shares one in-memory database across a run, so a prescription number
    issued by an earlier test is still there and the sequence hands out a duplicate.
    """

    import asyncio

    from sqlalchemy import delete, select, update

    from app.db.session import get_session_factory
    from app.models.prescription import Prescription
    from app.models.medicine import Medicine
    from app.models.number_sequence import NumberSequence
    from app.models.prescription_item import PrescriptionItem

    factory = get_session_factory()

    async def _go():
        async with factory() as db:
            # A prescription item carries a foreign key to Medicine, and foreign
            # keys are enforced. The medicine is seeded here rather than assumed,
            # because another module may have cleared the table.
            existing = (
                await db.execute(select(Medicine).where(Medicine.medicine_name == "Arnica Montana"))
            ).scalar_one_or_none()
            if existing is None:
                from datetime import UTC, datetime

                now = datetime.now(UTC)
                db.add(
                    Medicine(
                        medicine_code="QA-ARN",
                        medicine_name="Arnica Montana",
                        medicine_type="homoeopathic",
                        is_active=True,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await db.commit()

            await db.execute(delete(PrescriptionItem))
            await db.execute(delete(Prescription))
            # Reset the counter too: deleting the rows without rewinding the
            # sequence leaves the next number ahead of nothing, and a duplicate
            # arrives from whichever test ran first.
            await db.execute(
                update(NumberSequence)
                .where(NumberSequence.sequence_name == "prescription_number")
                .values(current_value=0)
            )
            await db.commit()

    asyncio.run(_go())


@pytest.fixture()
def client_with_prescription(isolated):
    from tests._qa_harness import auth_headers, make_client, seed_number_sequence, seed_visit

    with make_client() as client:
        _clear_prescriptions()
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        patient = client.post(
            "/api/v1/patients",
            headers=auth_headers(),
            json={"first_name": "Asha", "last_name": "Patel", "gender": "female"},
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["id"]

        visit_id, _number = seed_visit(patient_id=patient_id)
        seed_number_sequence(sequence_name="prescription_number", prefix="RX-")

        yield client, patient_id, visit_id


def test_a_prescription_carries_the_registration_number(client_with_prescription) -> None:
    """The client cannot print what it was never sent."""

    from tests._qa_harness import auth_headers

    client, _patient_id, visit_id = client_with_prescription

    created = client.post(
        "/api/v1/prescriptions",
        headers=auth_headers(),
        json={
            "visit_id": visit_id,
            "prescribed_by": 1,
            "prescription_datetime": "2026-11-10T09:00:00Z",
            "items": [
                {
                    "medicine_id": 1,
                    "dosage": "30C",
                    "frequency": "twice daily",
                    "quantity": 1,
                }
            ],
        },
    )
    assert created.status_code == 201, created.text

    read = client.get(
        f"/api/v1/prescriptions/{created.json()['id']}", headers=auth_headers()
    )

    assert read.status_code == 200, read.text
    body = read.json()
    assert "prescriber_registration" in body
    assert "prescriber_name" in body


def test_the_client_renders_the_header_from_what_it_is_sent() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    component = (root / "frontend" / "js" / "ui" / "prescription.js").read_text(
        encoding="utf-8"
    )
    assert "prescriber_registration" in component
    assert "Reg. No." in component
    assert "Registration number not recorded" in component

    clinical = (root / "frontend" / "js" / "clinical.js").read_text(encoding="utf-8")
    assert "prescriptionHeader(" in clinical, "the clinical screen must use the header"


def test_a_missing_number_is_shown_as_missing() -> None:
    """A blank line looks like an oversight; a stated absence is a prompt to fix it."""

    from pathlib import Path

    component = (
        Path(__file__).resolve().parents[2] / "frontend" / "js" / "ui" / "prescription.js"
    ).read_text(encoding="utf-8")
    assert "rx-registration-missing" in component
