"""Batch 84 — Laboratory Pending-Investigation Dashboard Feed contracts.

Locks in the surfaces that turn open laboratory orders into an actionable
dashboard feed:

* a dedicated /dashboard/pending-investigations endpoint surfacing live
  pending/in_progress orders oldest-first with per-order age in hours,
* the Batch 66 result-workflow status pair as the backlog definition
  (released reports flip orders to completed; cancelled orders never surface),
* the annual-lifecycle guard (archived-year rows never leak into the feed),
* response schemas exposing patient identity, OPD/IPD lineage and workload
  headline counts,
* frontend API wrapper and dashboard panel wired to the clinical workspace.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_pending_investigations_endpoint_wired_to_models():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/pending-investigations"' in src
    assert "from app.models.investigation import Investigation" in src
    # only live orders awaiting results surface; matched case-insensitively
    assert "Investigation.is_current_year.is_(True)" in src
    assert 'open_statuses = ("pending", "in_progress")' in src
    assert "func.lower(Investigation.investigation_status).in_(open_statuses)" in src
    # oldest-first backlog so ageing orders rise to the top
    assert "Investigation.requested_datetime.asc()" in src
    # batched patient enrichment (no N+1) plus age/headline fields
    assert "Patient.id.in_(patient_ids)" in src
    assert "age_hours" in src
    assert "pending_count" in src
    assert "in_progress_count" in src
    assert "CurrentUserDependency" in src


def test_pending_investigations_schemas_expose_actionable_fields():
    src = _read("backend/app/schemas/dashboard.py")
    assert "class PendingInvestigationItem(BaseSchema):" in src
    assert "class PendingInvestigationsResponse(BaseSchema):" in src
    for field in (
        "investigation_id",
        "patient_id",
        "patient_name",
        "patient_number",
        "case_type",
        "visit_id",
        "admission_id",
        "investigation_number",
        "investigation_name",
        "investigation_status",
        "requested_datetime",
        "requested_by",
        "age_hours",
    ):
        assert field in src
    assert "pending_count: int" in src
    assert "in_progress_count: int" in src
    assert '"PendingInvestigationItem"' in src and '"PendingInvestigationsResponse"' in src


def test_frontend_api_wrapper_targets_pending_investigations_route():
    src = _read("frontend/js/api.js")
    assert "export async function getDashboardPendingInvestigations" in src
    assert "/api/v1/dashboard/pending-investigations" in src


def test_dashboard_renders_pending_investigations_panel_with_handoff():
    src = _read("frontend/js/dashboard.js")
    assert "getDashboardPendingInvestigations" in src
    assert 'id="dashboard-pending-investigations"' in src
    assert "Pending investigations" in src
    # cards hand off into the patient clinical workspace
    assert "hhms:open-patient-clinical" in src
    # empty and failure states mirror the sibling panels
    assert "No investigations are awaiting results." in src
    assert "Pending investigations are unavailable right now." in src


def test_batch66_result_workflow_status_transitions_remain_intact():
    """The feed relies on released reports closing orders; keep that locked."""
    src = _read("backend/app/services/investigation_result.py")
    assert '"completed"' in src
    assert '"in_progress"' in src
    cancel_src = _read("backend/app/services/investigation.py")
    assert 'investigation_status="cancelled"' in cancel_src


def test_app_imports_and_exposes_pending_investigations_route():
    import sys

    sys.path.insert(0, str(ROOT / "backend"))
    from app.api.v1.api import api_router

    paths = {route.path for route in api_router.routes}
    assert "/dashboard/pending-investigations" in paths
