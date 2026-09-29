"""Batch 78 — Clinical cross-module workflow continuity contracts.

Static contract tests (consistent with the project's client-contract style)
that lock in the workflow-continuity surfaces introduced this batch:

* follow-up prescription lineage validation (previous/next prescription must
  exist and belong to the same patient's encounter history),
* due-follow-up window querying exposed through the service and API,
* case-wide prescription retrieval across a case record's encounters,
* frontend API wrappers for both new capabilities.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_followup_service_validates_prescription_lineage():
    src = _read("backend/app/services/followup.py")
    assert "_validate_prescription" in src
    # applied on both create and update paths
    assert src.count("_validate_prescription(") >= 4
    # lineage check spans existence + patient-scoped visit ownership
    assert "Prescription not found." in src
    assert "does not belong to this patient's encounter history." in src


def test_followup_service_exposes_due_window():
    src = _read("backend/app/services/followup.py")
    assert "async def list_due(" in src
    assert "next_followup_datetime" in src
    assert ".order_by(FollowUp.next_followup_datetime.asc()" in src


def test_followup_api_supports_due_window_and_case_query():
    src = _read("backend/app/api/v1/endpoints/followups.py")
    assert "due_from" in src and "due_to" in src
    assert "must be provided together" in src
    assert "list_due" in src
    assert "case_record_id" in src


def test_prescription_case_continuity_surfaces():
    repo = _read("backend/app/repositories/prescription.py")
    svc = _read("backend/app/services/prescription.py")
    api = _read("backend/app/api/v1/endpoints/prescriptions.py")
    assert "async def get_by_visits(" in repo
    assert "async def get_by_case(" in svc
    assert "/by-case/{case_record_id}" in api
    # route registered before the generic /{prescription_id} lookup route
    by_case_pos = api.index("/by-case/{case_record_id}")
    generic_pos = api.find('/"{prescription_id}"')
    assert generic_pos == -1 or by_case_pos < generic_pos


def test_frontend_api_wrappers_for_continuity():
    api = _read("frontend/js/api.js")
    assert "due_from" in api and "due_to" in api
    assert "/api/v1/prescriptions/by-case/" in api
