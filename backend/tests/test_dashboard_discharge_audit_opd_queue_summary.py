"""Batch 99 — Discharge Audit & OPD Queue Daily Summary contracts.

Locks in the two operational dashboard feeds delivered as the first
mega-batch under the amended batch policy (D-008):

* ``GET /dashboard/discharge-audit`` reconciles every recent discharge
  against its admission status and bed occupancy, so drifted ward-flow
  rows surface instead of silently disappearing;
* ``GET /dashboard/opd-queue-summary`` rolls live ``OPDToken`` rows up
  per queue day with a status split that always sums to the day total;
* shared pure derivations (``build_discharge_audit_result``,
  ``build_opd_queue_summary_result``) plus single-scan entry points so a
  future print envelope reuses the exact same numbers;
* response schemas exported from ``app.schemas.dashboard``;
* frontend API wrappers and dashboard panel wiring;
* documentation indexed in ``docs/INDEX.md``.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Pure derivation: discharge audit reconciliation
# ---------------------------------------------------------------------------


def _audit_row(**overrides):
    row = {
        "discharge_id": 1,
        "discharge_number": "DC-0001",
        "discharge_datetime": datetime(2026, 10, 4, 12, 0, 0),
        "discharge_status": "completed",
        "discharged_by": 7,
        "admission_id": 11,
        "admission_number": "AD-0011",
        "admission_status": "discharged",
        "patient_id": 21,
        "patient_name": "Ann Test",
        "patient_number": "P-0021",
        "bed_id": 31,
        "bed_number": "B-101",
        "ward": "General",
        "bed_occupancy_status": "available",
    }
    row.update(overrides)
    return row


def test_discharge_audit_result_reconciles_flags_and_headlines():
    from app.api.v1.endpoints.dashboard import build_discharge_audit_result

    as_of = datetime(2026, 10, 4, 15, 0, 0)
    rows = [
        _audit_row(),  # fully reconciled
        _audit_row(
            discharge_id=2,
            discharge_datetime=as_of - timedelta(hours=30),
            admission_status="active",
        ),  # admission never marked discharged
        _audit_row(
            discharge_id=3,
            discharge_datetime=as_of - timedelta(hours=3),
            bed_occupancy_status="occupied",
        ),  # bed never freed
        _audit_row(
            discharge_id=4,
            discharge_datetime=as_of - timedelta(hours=1),
            bed_id=None,
            bed_number=None,
            ward=None,
            bed_occupancy_status=None,
        ),  # no bed link at all
    ]
    result = build_discharge_audit_result(rows, as_of)

    assert result["total_discharges"] == 4
    assert result["reconciled_count"] + result["drift_count"] == result["total_discharges"]
    assert result["reconciled_count"] == 1
    assert result["drift_count"] == 3

    items = result["items"]
    # newest-discharge-first ordering (row 1 sits at noon, 3 hours before as_of)
    assert [item["discharge_id"] for item in items] == [4, 1, 3, 2]

    by_id = {item["discharge_id"]: item for item in items}
    assert by_id[1]["is_reconciled"] is True
    assert by_id[1]["hours_since_discharge"] == 3  # noon discharge vs 15:00 as_of
    assert by_id[2]["admission_discharged"] is False
    assert by_id[2]["is_reconciled"] is False
    assert by_id[3]["bed_freed"] is False
    assert by_id[3]["is_reconciled"] is False
    # missing bed link can never count as freed
    assert by_id[4]["bed_freed"] is False
    assert by_id[4]["is_reconciled"] is False


def test_discharge_audit_hours_never_negative_for_future_stamped_rows():
    from app.api.v1.endpoints.dashboard import build_discharge_audit_result

    as_of = datetime(2026, 10, 4, 12, 0, 0)
    result = build_discharge_audit_result(
        [_audit_row(discharge_datetime=as_of + timedelta(hours=5))], as_of
    )
    assert result["items"][0]["hours_since_discharge"] == 0


def test_discharge_audit_accepts_aware_datetimes():
    from app.api.v1.endpoints.dashboard import build_discharge_audit_result

    aware = datetime(2026, 10, 4, 10, 0, 0, tzinfo=timezone.utc)
    result = build_discharge_audit_result(
        [_audit_row(discharge_datetime=aware)],
        datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert result["items"][0]["hours_since_discharge"] == 2
    assert result["items"][0]["is_reconciled"] is True


# ---------------------------------------------------------------------------
# Pure derivation: OPD queue daily summary
# ---------------------------------------------------------------------------


def _token_row(queue_date, queue_status, token_count):
    return {
        "queue_date": queue_date,
        "queue_status": queue_status,
        "token_count": token_count,
    }


def test_opd_queue_summary_status_split_sums_to_day_total():
    from app.api.v1.endpoints.dashboard import build_opd_queue_summary_result

    day_a = date(2026, 10, 4)
    day_b = date(2026, 10, 3)
    rows = [
        _token_row(day_a, "waiting", 5),
        _token_row(day_a, "in_consultation", 2),
        _token_row(day_a, "completed", 9),
        _token_row(day_a, "cancelled", 1),
        _token_row(day_b, "WAITING", 3),  # case-insensitive statuses
        _token_row(day_b, "completed", 4),
    ]
    result = build_opd_queue_summary_result(rows, datetime(2026, 10, 4, 18, 0, 0))

    assert result["days_reported"] == 2
    assert result["total_tokens"] == 24
    assert result["total_open"] == 10
    items = result["items"]
    # newest queue day first
    assert [item["queue_date"] for item in items] == [day_a, day_b]
    for item in items:
        assert (
            item["waiting"]
            + item["in_consultation"]
            + item["completed"]
            + item["cancelled"]
            == item["total_tokens"]
        )
        assert item["open_token_count"] == item["waiting"] + item["in_consultation"]
    assert sum(item["total_tokens"] for item in items) == result["total_tokens"]
    assert items[0]["waiting"] == 5 and items[1]["waiting"] == 3


def test_opd_queue_summary_unknown_statuses_count_only_toward_totals():
    from app.api.v1.endpoints.dashboard import build_opd_queue_summary_result

    rows = [
        _token_row(date(2026, 10, 4), "waiting", 2),
        _token_row(date(2026, 10, 4), "mystery_state", 3),
    ]
    result = build_opd_queue_summary_result(rows, datetime(2026, 10, 4, 18, 0, 0))
    assert result["total_tokens"] == 5
    assert result["days_reported"] == 1
    # unknown status never inflates the split; it stays visible via totals
    assert result["items"][0]["total_tokens"] == 2


def test_opd_queue_summary_empty_scan_is_clean():
    from app.api.v1.endpoints.dashboard import build_opd_queue_summary_result

    result = build_opd_queue_summary_result([], datetime(2026, 10, 4, 18, 0, 0))
    assert result["items"] == []
    assert result["days_reported"] == 0
    assert result["total_tokens"] == 0
    assert result["total_open"] == 0


# ---------------------------------------------------------------------------
# Endpoint/schema wiring
# ---------------------------------------------------------------------------


def test_discharge_audit_endpoint_wired_to_models():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/discharge-audit"' in src
    assert "response_model=DischargeAuditResponse" in src
    assert "async def build_discharge_audit_scan" in src
    assert "build_discharge_audit_result(" in src
    # joined scan: discharge -> admission -> patient, bed outer-joined (no N+1)
    assert ".join(Admission, Admission.id == Discharge.admission_id)" in src
    assert ".join(Patient, Patient.id == Admission.patient_id)" in src
    assert ".outerjoin(Bed, Bed.id == Admission.bed_id)" in src
    # bounded window matching the other continuity feeds
    assert 'limit: int = Query(default=200, ge=1, le=500)' in src


def test_opd_queue_summary_endpoint_wired_to_grouped_scan():
    src = _read("backend/app/api/v1/endpoints/dashboard.py")
    assert '"/opd-queue-summary"' in src
    assert "response_model=OPDQueueSummaryResponse" in src
    assert "async def build_opd_queue_summary_scan" in src
    assert "build_opd_queue_summary_result(" in src
    assert "from app.models.opd_token import OPDToken" in src
    # one grouped pass over queue_date x queue_status, newest days only
    assert "func.count(OPDToken.id)" in src
    assert ".group_by(OPDToken.queue_date, OPDToken.queue_status)" in src
    assert "limit_days: int = Query(default=14, ge=1, le=90)" in src


def test_batch99_helpers_exported_from_dashboard_module():
    import app.api.v1.endpoints.dashboard as dashboard_module

    for name in (
        "build_discharge_audit_result",
        "build_discharge_audit_scan",
        "build_opd_queue_summary_result",
        "build_opd_queue_summary_scan",
    ):
        assert name in dashboard_module.__all__
        assert callable(getattr(dashboard_module, name))


def test_batch99_schemas_defined_and_exported():
    import app.schemas.dashboard as dashboard_schemas

    src = _read("backend/app/schemas/dashboard.py")
    for cls in (
        "DischargeAuditItem",
        "DischargeAuditResponse",
        "OPDQueueSummaryItem",
        "OPDQueueSummaryResponse",
    ):
        assert f"class {cls}(BaseSchema):" in src
        assert cls in dashboard_schemas.__all__

    for field in (
        "admission_discharged",
        "bed_freed",
        "hours_since_discharge",
        "is_reconciled",
        "reconciled_count",
        "drift_count",
    ):
        assert field in src

    for field in (
        "queue_date",
        "in_consultation",
        "open_token_count",
        "days_reported",
        "total_open",
    ):
        assert field in src


def test_batch99_schema_validation_round_trip():
    from app.schemas.dashboard import DischargeAuditResponse, OPDQueueSummaryResponse

    payload = DischargeAuditResponse(
        as_of=datetime(2026, 10, 4, 15, 0, 0),
        items=[
            {
                "discharge_id": 1,
                "discharge_number": "DC-0001",
                "discharge_datetime": datetime(2026, 10, 4, 12, 0, 0),
                "discharge_status": "completed",
                "discharged_by": 7,
                "admission_id": 11,
                "admission_number": "AD-0011",
                "admission_status": "discharged",
                "admission_discharged": True,
                "patient_id": 21,
                "patient_name": "Ann Test",
                "bed_id": 31,
                "bed_number": "B-101",
                "ward": "General",
                "bed_occupancy_status": "available",
                "bed_freed": True,
                "hours_since_discharge": 3,
                "is_reconciled": True,
            }
        ],
        total_discharges=1,
        reconciled_count=1,
        drift_count=0,
    )
    assert payload.items[0].is_reconciled is True

    queue = OPDQueueSummaryResponse(
        as_of=datetime(2026, 10, 4, 18, 0, 0),
        items=[
            {
                "queue_date": date(2026, 10, 4),
                "total_tokens": 10,
                "waiting": 4,
                "in_consultation": 1,
                "completed": 4,
                "cancelled": 1,
                "open_token_count": 5,
            }
        ],
        days_reported=1,
        total_tokens=10,
        total_open=5,
    )
    assert queue.items[0].open_token_count == 5


# ---------------------------------------------------------------------------
# Frontend wiring
# ---------------------------------------------------------------------------


def test_frontend_api_wrappers_target_batch99_routes():
    src = _read("frontend/js/api.js")
    assert "export async function getDashboardDischargeAudit" in src
    assert "/api/v1/dashboard/discharge-audit" in src
    assert "export async function getDashboardOPDQueueSummary" in src
    assert "/api/v1/dashboard/opd-queue-summary" in src


def test_dashboard_renders_batch99_panels():
    src = _read("frontend/js/dashboard.js")
    assert "getDashboardDischargeAudit" in src
    assert "getDashboardOPDQueueSummary" in src
    assert 'id="dashboard-discharge-audit"' in src
    assert 'id="dashboard-opd-queue-summary"' in src
    assert "Discharge audit" in src
    assert "OPD queue daily summary" in src
    # drift rows stay visible with actionable messages
    assert "Admission still active" in src
    assert "Bed still occupied" in src
    # cards hand off into the clinical workspace like the Batch 83 feed
    assert "hhms:open-patient-clinical" in src


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------


def test_batch99_documentation_exists_and_indexed():
    doc = ROOT / "docs" / "CLIENT_DISCHARGE_AUDIT_OPD_QUEUE_SUMMARY.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "/dashboard/discharge-audit" in text
    assert "/dashboard/opd-queue-summary" in text
    index = _read("docs/INDEX.md")
    assert "CLIENT_DISCHARGE_AUDIT_OPD_QUEUE_SUMMARY.md" in index
    changelog = _read("CHANGELOG.md")
    assert "Batch 99" in changelog


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
