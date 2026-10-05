"""Batch 101 contract tests — OPD queue & ward occupancy print envelopes.

Covers the operational print track added on top of the Batch 99 shared
derivations and the Batch 101 ward occupancy feed:

* ``build_ward_occupancy_summary_result`` invariants (pure derivation)
* Ward occupancy dashboard + print envelope schemas (fields, bounds,
  ``report_type`` discriminator, ``__all__`` exports)
* Endpoint/service wiring for ``POST /reports/ward-occupancy-print-envelope``
  (delegation to the shared scan/result builders for screen-paper parity)
* Frontend wiring: api wrapper, print preview renderer, reports card +
  handler imports, and the OPD queue summary card pairing
* Documentation indexing for the batch
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Pure derivation invariants
# ---------------------------------------------------------------------------


def test_ward_occupancy_rollup_status_split_invariant():
    from app.api.v1.endpoints.dashboard import build_ward_occupancy_summary_result

    rows = [
        {"bed_id": 1, "ward": "ICU", "occupancy_status": "Occupied",
         "has_active_admission": True, "length_of_stay_days": 5},
        {"bed_id": 2, "ward": "ICU", "occupancy_status": "reserved",
         "has_active_admission": False, "length_of_stay_days": None},
        {"bed_id": 3, "ward": "ICU", "occupancy_status": "available",
         "has_active_admission": False, "length_of_stay_days": None},
        {"bed_id": 4, "ward": None, "occupancy_status": "occupied",
         "has_active_admission": True, "length_of_stay_days": -3},
        {"bed_id": 5, "ward": "  ", "occupancy_status": "unknown-status",
         "has_active_admission": False, "length_of_stay_days": None},
    ]
    result = build_ward_occupancy_summary_result(rows, datetime(2026, 10, 5, 12))

    assert result["total_beds"] == 5
    # headline split foots against the master ledger
    assert (
        result["total_occupied"] + result["total_reserved"] + result["total_available"]
        == result["total_beds"]
    )
    assert result["total_occupied"] == 2
    assert result["total_reserved"] == 1
    assert result["total_available"] == 2  # includes unknown status remainder

    by_ward = {item["ward"]: item for item in result["items"]}
    icu = by_ward["ICU"]
    assert (
        icu["occupied_beds"] + icu["reserved_beds"] + icu["available_beds"]
        == icu["total_beds"]
    )
    assert icu["longest_stay_days"] == 5
    assert icu["active_admissions"] <= icu["occupied_beds"]

    # null/blank wards surface under the explicit Unassigned label
    unassigned = by_ward["Unassigned"]
    assert unassigned["total_beds"] == 2
    # negative stays clamped non-negative
    assert unassigned["longest_stay_days"] == 0
    assert result["wards_reported"] == len(result["items"])


def test_ward_occupancy_empty_rows_and_no_stay_none():
    from app.api.v1.endpoints.dashboard import build_ward_occupancy_summary_result

    result = build_ward_occupancy_summary_result([], datetime(2026, 10, 5, 12))
    assert result["items"] == []
    assert result["wards_reported"] == 0
    assert result["total_beds"] == 0

    # ward with beds but no live admission -> longest_stay_days is None, not 0
    only_reserved = build_ward_occupancy_summary_result(
        [{"bed_id": 9, "ward": "W2", "occupancy_status": "reserved",
          "has_active_admission": False, "length_of_stay_days": None}],
        datetime(2026, 10, 5, 12),
    )
    assert only_reserved["items"][0]["longest_stay_days"] is None


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


def test_batch101_schemas_exported():
    from app.schemas import reporting as reporting_schemas
    from app.schemas import dashboard as dashboard_schemas

    for name in (
        "WardOccupancyPrintRequest",
        "WardOccupancyPrintLine",
        "WardOccupancyPrintData",
        "WardOccupancyPrintEnvelope",
    ):
        assert name in reporting_schemas.__all__, name

    for name in ("WardOccupancySummaryItem", "WardOccupancySummaryResponse"):
        assert name in dashboard_schemas.__all__, name


def test_ward_occupancy_print_request_bounds_and_envelope_discriminator():
    from pydantic import ValidationError

    from app.schemas.reporting import (
        WardOccupancyPrintEnvelope,
        WardOccupancyPrintRequest,
    )

    field = WardOccupancyPrintRequest.model_fields["limit"]
    constraints = [repr(m) for m in field.metadata]
    assert any("ge=1" in c for c in constraints)
    assert any("le=2000" in c for c in constraints)

    with pytest.raises(ValidationError):
        WardOccupancyPrintRequest(limit=0)

    env_cls = WardOccupancyPrintEnvelope
    report_type = env_cls.model_fields["report_type"]
    assert report_type.default == "ward_occupancy_print"


def test_dashboard_ward_occupancy_response_shape():
    from app.schemas.dashboard import WardOccupancySummaryResponse

    fields = WardOccupancySummaryResponse.model_fields
    for name in (
        "as_of", "items", "wards_reported", "total_beds",
        "total_occupied", "total_reserved", "total_available",
        "total_active_admissions",
    ):
        assert name in fields, name


# ---------------------------------------------------------------------------
# Endpoint / service wiring
# ---------------------------------------------------------------------------


def test_ward_occupancy_routes_registered():
    from app.main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/v1/dashboard/ward-occupancy-summary" in paths
    assert "/api/v1/reports/ward-occupancy-print-envelope" in paths


def test_ward_occupancy_service_reuses_shared_builders():
    services = (REPO_ROOT / "backend/app/services/reporting.py").read_text()
    body = services[services.index("async def build_ward_occupancy_print_envelope"):]
    body = body[:body.index("\n    async def ")] if "\n    async def " in body else body
    assert "build_ward_occupancy_summary_scan" in body
    assert "build_ward_occupancy_summary_result" in body

    endpoints = (REPO_ROOT / "backend/app/api/v1/endpoints/reporting.py").read_text()
    assert '"/ward-occupancy-print-envelope"' in endpoints
    assert "WardOccupancyPrintEnvelope" in endpoints

    dashboard = (REPO_ROOT / "backend/app/api/v1/endpoints/dashboard.py").read_text()
    assert '"/ward-occupancy-summary"' in dashboard
    assert '"build_ward_occupancy_summary_result"' in dashboard
    assert '"build_ward_occupancy_summary_scan"' in dashboard


# ---------------------------------------------------------------------------
# Frontend wiring
# ---------------------------------------------------------------------------


def test_frontend_batch101_wrappers_and_renderers():
    api = (REPO_ROOT / "frontend/js/api.js").read_text()
    assert "getDashboardWardOccupancySummary" in api
    assert "ward-occupancy-summary" in api
    assert "buildWardOccupancyPrintEnvelope" in api
    assert "ward-occupancy-print-envelope" in api

    print_js = (REPO_ROOT / "frontend/js/print.js").read_text()
    assert re.search(
        r"export function createWardOccupancyPrintPreview\(host,\{envelope=null,data=null",
        print_js,
    )
    assert "createOPDQueueSummaryPrintPreview" in print_js


def test_reports_workspace_cards_wired():
    reports = (REPO_ROOT / "frontend/js/reports.js").read_text()
    # imports
    assert "buildWardOccupancyPrintEnvelope" in reports.splitlines()[0]
    assert "createWardOccupancyPrintPreview" in reports.splitlines()[0]
    assert "buildOPDQueueSummaryPrintEnvelope" in reports.splitlines()[0]
    assert "createOPDQueueSummaryPrintPreview" in reports.splitlines()[0]
    # cards (single-escaped id convention inside the template literal)
    for token in (
        "ward-occupancy-limit",
        "ward-occupancy-prepare",
        "ward-occupancy-note",
        "queue-summary-days",
        "queue-summary-prepare",
    ):
        assert token in reports, token
    # handlers post through the envelopes and render previews
    assert "await buildWardOccupancyPrintEnvelope({limit,title:\"Ward Occupancy Summary\"})" in reports
    assert "createWardOccupancyPrintPreview($(\"#print-preview-host\",box),{envelope})" in reports
    assert "await buildOPDQueueSummaryPrintEnvelope({limit_days:limitDays" in reports


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------


def test_batch101_documented():
    index = (REPO_ROOT / "docs/INDEX.md").read_text()
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    state = (REPO_ROOT / ".ai/PROJECT_STATE.md").read_text()
    assert "Batch 101" in index or "batch101" in index.lower()
    assert "Batch 101" in changelog
    assert "Batch 101" in state
