"""Batch 102 contract tests — investigation billing reconciliation.

Covers the lab/billing boundary batch that reconciles every open
investigation order (Batch 84 pending vocabulary) against live
``InvoiceItem`` lines:

* ``_invoice_line_investigation_key`` reference-token matching
* ``build_investigation_billing_reconciliation_result`` invariants
  (pure derivation, shared verbatim by dashboard + print envelope)
* Dashboard + print envelope schemas (fields, bounds, ``report_type``
  discriminator, ``__all__`` exports)
* Endpoint/service wiring for
  ``POST /reports/investigation-billing-reconciliation-print-envelope``
  (delegation to the shared scan/result builders for screen-paper parity)
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Invoice-line reference matching
# ---------------------------------------------------------------------------


def test_invoice_line_reference_token_matching():
    from app.api.v1.endpoints.dashboard import _invoice_line_investigation_key

    assert _invoice_line_investigation_key("Investigation:42 CBC panel") == 42
    assert _invoice_line_investigation_key("investigation : 7") == 7
    # legacy free-text keyword forms still reconcile
    assert _invoice_line_investigation_key("Investigation No 15") == 15
    assert _invoice_line_investigation_key("investigation id=99") == 99
    # unmatched lines simply never match (drift-surfacing philosophy)
    assert _invoice_line_investigation_key("Consultation fee") is None
    assert _invoice_line_investigation_key(None) is None
    assert _invoice_line_investigation_key("") is None


# ---------------------------------------------------------------------------
# Pure derivation invariants
# ---------------------------------------------------------------------------


def _row(inv_id: int, status: str, charged: str, credited: str, items: int = 1):
    return {
        "investigation_id": inv_id,
        "patient_id": 100 + inv_id,
        "patient_name": f"Patient {inv_id}",
        "patient_number": f"P-{inv_id}",
        "case_type": "OPD",
        "visit_id": None,
        "admission_id": None,
        "investigation_number": f"INV-{inv_id}",
        "investigation_name": "CBC",
        "investigation_status": status,
        "requested_datetime": datetime(2026, 10, 5, 0, 0),
        "charged_total": Decimal(charged),
        "credited_total": Decimal(credited),
        "invoice_item_count": items,
    }


def test_investigation_billing_rollup_invariants():
    from app.api.v1.endpoints.dashboard import (
        build_investigation_billing_reconciliation_result,
    )

    rows = [
        _row(1, "pending", "250.00", "0"),          # billed
        _row(2, "in_progress", "0", "0"),           # unbilled -> surfaces with 0
        _row(3, "pending", "500.00", "100.00"),     # partial credit
        _row(4, "PENDING", "120.00", "120.00"),     # fully credited -> missing
    ]
    as_of = datetime(2026, 10, 5, 12)
    result = build_investigation_billing_reconciliation_result(rows, as_of)

    # headline splits foot against the master ledger
    assert result["total_investigations_checked"] == 4
    assert (
        result["pending_count"] + result["in_progress_count"]
        == result["total_investigations_checked"]
    )
    assert (
        result["billed_count"] + result["billed_missing_count"]
        == result["total_investigations_checked"]
    )
    assert result["pending_count"] == 3
    assert result["in_progress_count"] == 1
    assert result["billed_count"] == 2
    assert result["billed_missing_count"] == 2

    by_id = {item["investigation_id"]: item for item in result["items"]}
    for item in by_id.values():
        # per-row invariant holds by construction
        assert item["billed_amount"] == item["charged_total"] - item["credited_total"]
        assert item["is_billed"] == (item["billed_amount"] > 0)
        assert item["is_billed_missing"] == (not item["is_billed"])
        assert item["age_hours"] >= 0

    assert by_id[2]["billed_amount"] == Decimal("0")
    assert by_id[2]["is_billed_missing"] is True  # unbilled stays visible
    assert by_id[3]["billed_amount"] == Decimal("400.00")
    assert by_id[4]["billed_amount"] == Decimal("0")

    total_billed = sum(i["billed_amount"] for i in result["items"])
    assert result["total_billed"] == total_billed


def test_investigation_billing_empty_rows_headline_zero():
    from app.api.v1.endpoints.dashboard import (
        build_investigation_billing_reconciliation_result,
    )

    result = build_investigation_billing_reconciliation_result(
        [], datetime(2026, 10, 5, 12)
    )
    assert result["items"] == []
    assert result["total_investigations_checked"] == 0
    assert result["pending_count"] == 0
    assert result["in_progress_count"] == 0
    assert result["billed_count"] == 0
    assert result["billed_missing_count"] == 0
    assert result["total_billed"] == Decimal("0")


def test_investigation_billing_age_hours_naive_and_tz():
    from datetime import timezone

    from app.api.v1.endpoints.dashboard import (
        build_investigation_billing_reconciliation_result,
    )

    tz_row = _row(5, "pending", "10", "0")
    tz_row["requested_datetime"] = datetime(
        2026, 10, 5, 6, 0, tzinfo=timezone.utc
    )
    future_row = _row(6, "pending", "10", "0")
    future_row["requested_datetime"] = datetime(2026, 10, 5, 18, 0)
    as_of = datetime(2026, 10, 5, 12)
    result = build_investigation_billing_reconciliation_result(
        [tz_row, future_row], as_of
    )
    by_id = {item["investigation_id"]: item for item in result["items"]}
    assert by_id[5]["age_hours"] == 6
    assert by_id[6]["age_hours"] == 0  # clamped non-negative


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


def test_batch102_schemas_exported():
    from app.schemas import reporting as reporting_schemas
    from app.schemas import dashboard as dashboard_schemas

    for name in (
        "InvestigationBillingReconciliationPrintRequest",
        "InvestigationBillingReconciliationPrintLine",
        "InvestigationBillingReconciliationPrintData",
        "InvestigationBillingReconciliationPrintEnvelope",
    ):
        assert name in reporting_schemas.__all__, name

    for name in (
        "InvestigationBillingReconciliationItem",
        "InvestigationBillingReconciliationResponse",
    ):
        assert name in dashboard_schemas.__all__, name


def test_investigation_billing_print_request_bounds_and_discriminator():
    from pydantic import ValidationError

    from app.schemas.reporting import (
        InvestigationBillingReconciliationPrintEnvelope,
        InvestigationBillingReconciliationPrintRequest,
    )

    field = InvestigationBillingReconciliationPrintRequest.model_fields["limit"]
    constraints = [repr(m) for m in field.metadata]
    assert any("ge=1" in c for c in constraints)
    assert any("le=1000" in c for c in constraints)

    with pytest.raises(ValidationError):
        InvestigationBillingReconciliationPrintRequest(limit=0)

    report_type = InvestigationBillingReconciliationPrintEnvelope.model_fields[
        "report_type"
    ]
    assert report_type.default == "investigation_billing_reconciliation_print"


def test_dashboard_investigation_billing_response_shape():
    from app.schemas.dashboard import InvestigationBillingReconciliationResponse

    fields = InvestigationBillingReconciliationResponse.model_fields
    for name in (
        "as_of",
        "currency_note",
        "items",
        "total_investigations_checked",
        "pending_count",
        "in_progress_count",
        "billed_count",
        "billed_missing_count",
        "total_billed",
    ):
        assert name in fields, name


# ---------------------------------------------------------------------------
# Endpoint / service wiring
# ---------------------------------------------------------------------------


def test_investigation_billing_routes_registered():
    from app.main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/v1/dashboard/investigation-billing-reconciliation" in paths
    assert (
        "/api/v1/reports/investigation-billing-reconciliation-print-envelope"
        in paths
    )


def test_investigation_billing_service_reuses_shared_builders():
    services = (REPO_ROOT / "backend/app/services/reporting.py").read_text()
    body = services[
        services.index(
            "async def build_investigation_billing_reconciliation_print_envelope"
        ):
    ]
    body = body[: body.index("\n    async def ")] if "\n    async def " in body else body
    assert "build_investigation_billing_reconciliation_scan" in body
    assert "build_investigation_billing_reconciliation_result" in body

    endpoints = (REPO_ROOT / "backend/app/api/v1/endpoints/reporting.py").read_text()
    assert '"/investigation-billing-reconciliation-print-envelope"' in endpoints
    assert "InvestigationBillingReconciliationPrintEnvelope" in endpoints

    dashboard = (REPO_ROOT / "backend/app/api/v1/endpoints/dashboard.py").read_text()
    assert '"/investigation-billing-reconciliation"' in dashboard
    assert '"build_investigation_billing_reconciliation"' in dashboard
    assert '"build_investigation_billing_reconciliation_result"' in dashboard
    assert '"build_investigation_billing_reconciliation_scan"' in dashboard
