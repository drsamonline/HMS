"""Batch 103 (Milestone 6) — Cross-module integration E2E suite.

Chains real HTTP routes across modules over one shared in-memory schema,
using the Batch 103 QA harness seed helpers:

* Patient registration -> Visit creation -> OPD token generation -> queue
  progression (waiting -> called -> completed) -> queue visibility via
  ``GET /opd-tokens`` and the Batch 100 OPD-queue-summary dashboard feed.
* Duplicate-token guard surfaced as a handled 4xx (never 500).
* Dashboard feeds reflect seeded data (no crash on warm state), closing
  the cold-state gap left by the empty-database probe in
  ``test_batch103_qa_end_to_end.py``.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from _qa_harness import (  # noqa: E402
    api_get,
    api_post,
    api_put,
    make_client,
    seed_number_sequence,
    seed_user,
    seed_visit,
)


def _today() -> str:
    return date.today().isoformat()


def test_patient_visit_token_chain_end_to_end():
    """Full OPD journey over HTTP: register patient, seed visit, mint
    token, progress queue status, and see it on the queue list + summary."""
    with make_client() as client:
        seed_user()
        seed_number_sequence(sequence_name="patient_number", prefix="P-")

        # 1. Register the patient through the API.
        patient = api_post(
            client,
            "/patients",
            json={
                "first_name": "Integration",
                "last_name": "Case",
                "gender": "Female",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["id"]
        assert patient.json()["patient_number"] == "P-0001"

        # 2. Seed the clinical visit (direct insert; harness maintains the
        #    visit_number sequence so the V- identity stays realistic).
        visit_id, visit_number = seed_visit(patient_id=patient_id)
        assert visit_number == "V-0001"

        # The visit is visible through its own module route.
        fetched = api_get(client, f"/visits/{visit_id}")
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["patient_id"] == patient_id

        # 3. Generate the OPD token for the visit.
        token = api_post(
            client,
            "/opd-tokens",
            json={"visit_id": visit_id, "queue_date": _today()},
        )
        assert token.status_code == 201, token.text
        created = token.json()
        token_id = created["id"]
        assert created["token_number"] == 1
        assert created["queue_status"] == "waiting"

        # 4. Duplicate token for the same visit must be rejected cleanly.
        dup = api_post(
            client,
            "/opd-tokens",
            json={"visit_id": visit_id, "queue_date": _today()},
        )
        assert dup.status_code in (400, 409), dup.text
        assert dup.status_code != 500

        # 5. Progress the queue: waiting -> called -> completed.
        now_iso = datetime.now(timezone.utc).isoformat()
        called = api_put(
            client,
            f"/opd-tokens/{token_id}",
            json={"queue_status": "called", "called_at": now_iso},
        )
        assert called.status_code == 200, called.text
        assert called.json()["queue_status"] == "called"

        completed = api_put(
            client,
            f"/opd-tokens/{token_id}",
            json={"queue_status": "completed", "completed_at": now_iso},
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["queue_status"] == "completed"

        # 6. Queue list shows exactly our token for today's date.
        listing = api_get(
            client, "/opd-tokens", params={"queue_date": _today()}
        )
        assert listing.status_code == 200, listing.text
        rows = listing.json()
        assert len(rows) == 1
        assert rows[0]["id"] == token_id
        assert rows[0]["queue_status"] == "completed"

        # 7. Batch 100 OPD-queue-summary dashboard feed reflects warm data.
        summary = api_get(client, "/dashboard/opd-queue-summary")
        assert summary.status_code == 200, summary.text
        body = summary.json()
        assert isinstance(body, dict)


def test_dashboard_feeds_respond_on_warm_seeded_state():
    """All audit/dashboard feeds (Batches 98-102) answer 200 once core
    records exist — guards against aggregate queries crashing on joins
    with live rows, which the cold-state probe cannot cover."""
    feeds = [
        "/dashboard/due-followups",
        "/dashboard/outstanding-invoices",
        "/dashboard/bed-occupancy",
        "/dashboard/pending-investigations",
        "/dashboard/receivables-aging",
        "/dashboard/invoice-receipt-continuity",
        "/dashboard/receipt-numbering-continuity",
        "/dashboard/invoice-payment-reconciliation",
        "/dashboard/payment-method-summary",
        "/dashboard/invoice-overpayments",
        "/dashboard/discharge-audit",
        "/dashboard/opd-queue-summary",
        "/dashboard/refund-audit",
        "/dashboard/investigation-billing-reconciliation",
    ]
    with make_client() as client:
        seed_user()
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        patient = api_post(
            client,
            "/patients",
            json={
                "first_name": "Warm",
                "last_name": "Probe",
                "gender": "Male",
            },
        )
        assert patient.status_code == 201, patient.text
        visit_id, _ = seed_visit(patient_id=patient.json()["id"])
        api_post(
            client,
            "/opd-tokens",
            json={"visit_id": visit_id, "queue_date": _today()},
        )

        failures = []
        for feed in feeds:
            resp = api_get(client, feed)
            if resp.status_code != 200 or not isinstance(resp.json(), dict):
                failures.append((feed, resp.status_code, resp.text[:200]))
        assert not failures, f"feeds failed on warm state: {failures}"
