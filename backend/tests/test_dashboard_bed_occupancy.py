"""Batch 83 — IPD Bed-Occupancy Continuity contracts.

Locks in the surfaces that turn bed/admission state into an actionable
inpatient dashboard feed:

* a dedicated /dashboard/bed-occupancy endpoint reconciling occupied beds
  against active admissions (batched enrichment, no N+1),
* response schemas exposing ward identity, admission lineage and length of
  stay so occupancy is actionable from the dashboard,
* frontend API wrapper and dashboard panel wired to the clinical workspace,
* reliance on the Batch 61 concurrency guarantees (single active admission
  per bed via row locking + partial unique index).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_bed_occupancy_endpoint_wired_to_models():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/bed-occupancy"' in src
    assert "from app.models.admission import Admission" in src
    assert "from app.models.bed import Bed" in src
    # only live, non-released beds surface; occupancy matched case-insensitively
    assert "Bed.is_active.is_(True)" in src
    assert 'func.lower(Bed.occupancy_status).in_(("occupied", "reserved"))' in src
    # active-admission reconciliation mirrors the Batch 61 status pair
    assert 'func.lower(Admission.admission_status).in_(active_statuses)' in src
    assert 'active_statuses = ("admitted", "active")' in src
    # batched lookups (no N+1) plus enrichment fields
    assert "Admission.bed_id.in_(bed_ids)" in src
    assert "Patient.id.in_(patient_ids)" in src
    assert "length_of_stay_days" in src
    assert "has_active_admission" in src
    assert "CurrentUserDependency" in src


def test_bed_occupancy_schemas_expose_reconciliation_fields():
    src = _read("backend/app/schemas/dashboard.py")
    assert "class BedOccupancyItem(BaseSchema):" in src
    assert "class BedOccupancyResponse(BaseSchema):" in src
    for field in (
        "bed_id",
        "bed_number",
        "ward",
        "occupancy_status",
        "has_active_admission",
        "admission_id",
        "admission_number",
        "admission_datetime",
        "patient_id",
        "patient_name",
        "patient_number",
        "length_of_stay_days",
    ):
        assert field in src
    assert "occupied_count: int" in src
    assert "total_beds: int" in src
    assert '"BedOccupancyItem"' in src and '"BedOccupancyResponse"' in src


def test_frontend_api_wrapper_targets_bed_occupancy_route():
    src = _read("frontend/js/api.js")
    assert "export async function getDashboardBedOccupancy" in src
    assert "/api/v1/dashboard/bed-occupancy" in src


def test_dashboard_renders_bed_occupancy_panel_with_handoff():
    src = _read("frontend/js/dashboard.js")
    assert "getDashboardBedOccupancy" in src
    assert 'id="dashboard-bed-occupancy"' in src
    assert "IPD bed occupancy" in src
    # cards hand off into the patient clinical workspace
    assert "hhms:open-patient-clinical" in src
    # drift rows stay visible instead of silently disappearing
    assert "no active admission" in src
    # graceful unavailable-state like the sibling panels
    assert "Bed occupancy is unavailable right now." in src


def test_batch61_concurrency_guarantees_remain_intact():
    """The feed relies on one-active-admission-per-bed; keep that locked."""
    repo_src = _read("backend/app/repositories/admission.py")
    assert "get_active_for_bed_for_update" in repo_src
    svc_src = _read("backend/app/services/admission.py")
    assert "Selected bed already has an active admission." in svc_src
    discharge_src = _read("backend/app/services/discharge.py")
    assert 'admission.admission_status = (' in discharge_src or 'admission_status = "discharged"' in discharge_src.replace("\n", " ")
