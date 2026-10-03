"""Batch 84 — Laboratory Pending-Investigation Continuity contracts.

Locks in the surfaces that turn outstanding laboratory workload into an
actionable dashboard feed:

* a dedicated /dashboard/pending-investigations endpoint selecting only the
  non-terminal Batch 66 states (pending/in_progress), oldest-first,
* response schemas exposing order identity, patient enrichment and age so
  the backlog is prioritisable from the dashboard,
* frontend API wrapper and dashboard panel wired to the clinical workspace,
* reliance on the Batch 66 monotonic result workflow (verification moves
  orders to in_progress, release completes them).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_pending_investigations_endpoint_wired_to_models():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/pending-investigations"' in src
    assert "from app.models.investigation import Investigation" in src
    # only the two non-terminal Batch 66 states surface
    assert 'outstanding_statuses = ("pending", "in_progress")' in src
    assert "func.lower(Investigation.investigation_status).in_(outstanding_statuses)" in src
    # oldest-first prioritisation of the backlog
    assert "Investigation.requested_datetime.asc()" in src
    # batched patient lookup (no N+1) plus derived age
    assert "Patient.id.in_(patient_ids)" in src
    assert "age_hours" in src
    assert "CurrentUserDependency" in src


def test_pending_investigations_schemas_expose_workload_fields():
    src = _read("backend/app/schemas/dashboard.py")
    assert "class PendingInvestigationItem(BaseSchema):" in src
    assert "class PendingInvestigationsResponse(BaseSchema):" in src
    for field in (
        "investigation_id",
        "investigation_number",
        "patient_id",
        "patient_name",
        "patient_number",
        "investigation_name",
        "investigation_status",
        "requested_datetime",
        "requested_by",
        "visit_id",
        "admission_id",
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
    # headline workload counts
    assert "pending_count" in src
    assert "in_progress_count" in src
    # cards hand off into the patient clinical workspace like sibling panels
    assert "hhms:open-patient-clinical" in src
    # graceful unavailable-state like the sibling panels
    assert "Pending investigations are unavailable right now." in src


def test_batch66_result_workflow_remains_the_status_source():
    """The feed relies on pending -> in_progress -> completed; keep it locked."""
    svc_src = _read("backend/app/services/investigation_result.py")
    # verification advances the source investigation to in_progress
    assert '"in_progress"' in svc_src
    # release completes it; released reports are immutable
    assert "released" in svc_src
    model_src = _read("backend/app/models/investigation.py")
    assert "investigation_status" in model_src
    schema_src = _read("backend/app/schemas/investigation.py")
    assert '"pending",' in schema_src
    assert '"in_progress",' in schema_src
    assert '"completed",' in schema_src
    assert '"cancelled",' in schema_src
