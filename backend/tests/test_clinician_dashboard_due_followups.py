"""Batch 79 — Clinician dashboard due-follow-up workflow continuity contracts.

Locks in the surfaces that turn the Batch 78 due-window service query into an
actionable clinician dashboard feed:

* a dedicated /dashboard/due-followups endpoint with patient/case enrichment,
* router registration on the v1 API surface (import AND include),
* response schema exposing actionable identity fields,
* frontend API wrapper and dashboard rendering wired to the clinical workspace,
* follow-up form capturing next_followup_datetime so due lists have data.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dashboard_endpoint_module_exists():
    assert (ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "dashboard.py").is_file()
    assert (ROOT / "backend" / "app" / "schemas" / "dashboard.py").is_file()


def test_dashboard_endpoint_uses_due_window_service():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert 'prefix="/dashboard"' in src
    assert '"/due-followups"' in src
    assert "followup_service.list_due" in src
    # enrichment joins so clinicians see patient/case identity, not bare IDs
    assert "patient_name" in src
    assert "case_number" in src
    assert "CurrentUserDependency" in src


def test_dashboard_router_registered_on_api():
    src = _read("backend/app/api/v1/api.py")
    assert "from app.api.v1.endpoints.dashboard import router as dashboard_router" in src
    assert "include_router(dashboard_router)" in src


def test_dashboard_schemas_expose_actionable_fields():
    src = _read("backend/app/schemas/dashboard.py")
    for field in (
        "followup_id",
        "case_record_id",
        "patient_id",
        "patient_name",
        "next_followup_datetime",
    ):
        assert field in src
    assert "class DueFollowUpsResponse" in src


def test_frontend_wrapper_and_dashboard_rendering():
    api = _read("frontend/js/api.js")
    dash = _read("frontend/js/dashboard.js")
    assert "/api/v1/dashboard/due-followups" in api
    assert "getDashboardDueFollowups" in api
    assert "getDashboardDueFollowups" in dash
    # clicking a due follow-up hands off to the clinical workspace event
    assert "hhms:open-patient-clinical" in dash


def test_followup_form_captures_next_due_datetime():
    src = _read("frontend/js/clinical.js")
    assert 'name="next_followup_datetime"' in src
    # saved follow-ups display their scheduled next visit
    assert "next_followup_datetime" in src


def test_app_imports_and_exposes_dashboard_route():
    import sys

    sys.path.insert(0, str(ROOT / "backend"))
    from app.api.v1.api import api_router

    paths = {route.path for route in api_router.routes}
    assert "/dashboard/due-followups" in paths
