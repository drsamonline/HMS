"""Gate tests for the lab accession slice.

An order becomes a sample. The laboratory writes its own identifier on the tube, and
that identifier - not the hospital's investigation number - is how a result is traced
back to what was collected.

Two properties: an accession round-trips, and two specimens cannot share one.
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


def _patient(client) -> int:
    from tests._qa_harness import auth_headers, seed_number_sequence

    seed_number_sequence(sequence_name="patient_number", prefix="P-")
    response = client.post(
        "/api/v1/patients",
        headers=auth_headers(),
        json={"first_name": "Asha", "last_name": "Patel", "gender": "female"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _investigation(client, patient_id: int, accession: str | None):
    from tests._qa_harness import auth_headers, seed_visit

    visit_id, _number = seed_visit(patient_id=patient_id)
    payload = {
        "patient_id": patient_id,
        "visit_id": visit_id,
        "investigation_name": "Complete blood count",
        "requested_by": 1,
        "requested_datetime": "2026-11-10T09:00:00Z",
    }
    if accession is not None:
        payload["sample_accession"] = accession
    return client.post("/api/v1/investigations", headers=auth_headers(), json=payload)


def test_an_accession_round_trips(isolated) -> None:
    from tests._qa_harness import auth_headers, make_client, seed_number_sequence

    with make_client() as client:
        seed_number_sequence(sequence_name="investigation_number", prefix="INV-")
        patient_id = _patient(client)

        created = _investigation(client, patient_id, "LAB-2026-000123")
        assert created.status_code == 201, created.text
        investigation_id = created.json()["id"]

        read = client.get(
            f"/api/v1/investigations/{investigation_id}", headers=auth_headers()
        )

    assert read.status_code == 200, read.text
    assert read.json()["sample_accession"] == "LAB-2026-000123"


def test_a_duplicate_accession_is_refused(isolated) -> None:
    """Two specimens sharing an accession is a mix-up, not a duplicate."""

    from tests._qa_harness import make_client, seed_number_sequence

    with make_client() as client:
        seed_number_sequence(sequence_name="investigation_number", prefix="INV-")
        patient_id = _patient(client)

        first = _investigation(client, patient_id, "LAB-2026-000123")
        assert first.status_code == 201, first.text

        second = _investigation(client, patient_id, "LAB-2026-000123")

    assert second.status_code in (400, 409, 422), second.text
    assert "already on another specimen" in second.text


def test_an_investigation_without_a_sample_is_still_allowed(isolated) -> None:
    """A hospital with no laboratory never sets one."""

    from tests._qa_harness import make_client, seed_number_sequence

    with make_client() as client:
        seed_number_sequence(sequence_name="investigation_number", prefix="INV-")
        patient_id = _patient(client)
        response = _investigation(client, patient_id, None)

    assert response.status_code == 201, response.text
    assert response.json()["sample_accession"] is None


def test_the_worklist_can_be_drawn_by_status(isolated) -> None:
    """The status filter already existed; this records that it is the worklist."""

    from tests._qa_harness import auth_headers, make_client

    with make_client() as client:
        response = client.get(
            "/api/v1/investigations",
            headers=auth_headers(),
            params={"investigation_status": "requested"},
        )

    assert response.status_code == 200, response.text
