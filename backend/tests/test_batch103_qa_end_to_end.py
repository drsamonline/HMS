"""Batch 103 (Milestone 6) — Comprehensive QA end-to-end route suite.

Exercises real HTTP routes through the full FastAPI stack (middleware,
exception handlers, auth dependency, service layer, async SQLAlchemy on
in-memory SQLite) using the shared ``_qa_harness`` environment.

Codifies the findings from the Batch 103 QA pass:

* ``POST /auth/login`` must return 200 + bearer token for valid seeded
  credentials and a structured 401 for bad credentials — this regression
  guarded the ``user.hashed_password`` -> ``user.password_hash`` product
  bug found and fixed during Batch 103.
* Unauthenticated requests are rejected with 401; JWT-authenticated
  reads succeed.
* Patient lifecycle writes mint sequence numbers (``P-0001``) and apply
  text normalization end-to-end.
* Every dashboard operational feed — including the Batch 99-102 audit
  surfaces — answers 200 on an empty database (no crash on cold state).
"""
from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from _qa_harness import (  # noqa: E402
    api_get,
    api_post,
    make_client,
    seed_number_sequence,
    seed_user,
)

API = "/api/v1"

# All 14 GET feeds registered on the dashboard router (verified against
# the @router.get decorators in app/api/v1/endpoints/dashboard.py).
DASHBOARD_FEEDS = [
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
    "/dashboard/discharge-audit",                # Batch 99
    "/dashboard/opd-queue-summary",              # Batch 100
    "/dashboard/refund-audit",                   # Batch 100
    "/dashboard/investigation-billing-reconciliation",  # Batch 102
]


def test_health_live_is_public():
    """Liveness probe works without auth and reports healthy."""
    with make_client() as client:
        resp = client.get(f"{API}/health/live")
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "healthy"


def test_login_success_returns_bearer_token():
    """Regression guard: login crashed with 500 when auth service read a
    non-existent ``hashed_password`` attribute instead of the model's
    ``password_hash`` column (product bug found by this Batch 103 suite).

    Seed + login must share one ``make_client()`` block because the
    in-memory SQLite schema is recreated fresh on every harness entry.
    """
    with make_client() as client:
        uid = seed_user(username="qa-second", password="qa-secret-123")
        resp = client.post(
            f"{API}/auth/login",
            json={"username": "qa-second", "password": "qa-secret-123"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20
        assert uid > 0


def test_login_bad_credentials_returns_structured_401():
    with make_client() as client:
        seed_user(username="qa-admin", password="qa-password")
        resp = client.post(
            f"{API}/auth/login",
            json={"username": "qa-admin", "password": "wrong-password"},
        )
        assert resp.status_code == 401, resp.text
        body = resp.json()
        # Structured error envelope (not a raw traceback / 500).
        assert "detail" in body or "message" in body or "error" in body


def test_me_requires_valid_token():
    with make_client() as client:
        seed_user(username="qa-admin", password="qa-password")
        login = client.post(
            f"{API}/auth/login",
            json={"username": "qa-admin", "password": "qa-password"},
        )
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]

        me = client.get(
            f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me.status_code == 200, me.text
        assert me.json()["username"] == "qa-admin"


def test_unauthenticated_requests_are_rejected():
    with make_client() as client:
        resp = client.get(f"{API}/patients")
        assert resp.status_code == 401, resp.text
        dash = client.get(f"{API}/dashboard/refund-audit")
        assert dash.status_code == 401, dash.text


def test_invalid_token_is_rejected():
    with make_client() as client:
        resp = client.get(
            f"{API}/patients",
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )
        assert resp.status_code == 401, resp.text


def test_patient_lifecycle_end_to_end():
    """Create (sequence-minted number + text normalization), get, list+search."""
    with make_client() as client:
        seed_user()
        seed_number_sequence(sequence_name="patient_number", prefix="P-")

        create = api_post(
            client,
            "/patients",
            json={
                "first_name": "QA ",          # trailing space -> normalized
                "last_name": "Patient",
                "gender": " Male ",           # padded -> normalized
            },
        )
        assert create.status_code == 201, create.text
        created = create.json()
        pid = created["id"]
        assert created["patient_number"] == "P-0001"
        assert created["first_name"] == "QA"
        assert created["gender"] == "Male"

        fetch = api_get(client, f"/patients/{pid}")
        assert fetch.status_code == 200, fetch.text
        assert fetch.json()["patient_number"] == "P-0001"

        listing = api_get(client, "/patients", params={"search": "QA"})
        assert listing.status_code == 200, listing.text
        rows = listing.json()
        assert any(r["id"] == pid for r in rows)

        miss = api_get(client, "/patients", params={"search": "zzz-no-match"})
        assert miss.status_code == 200, miss.text
        assert miss.json() == []


def test_patient_create_without_sequence_is_clean_error():
    """Missing NumberSequence config must surface as a handled error, not 500."""
    with make_client() as client:
        seed_user()
        create = api_post(
            client,
            "/patients",
            json={"first_name": "No", "last_name": "Seq", "gender": "Female"},
        )
        # ResourceNotFound maps to 404 via the exception handlers.
        assert create.status_code == 404, create.text


def test_dashboard_feeds_all_respond_on_empty_database():
    """Every dashboard GET feed (incl. Batch 99-102 audit surfaces) must
    answer 200 with a well-formed envelope on cold/empty state."""
    with make_client() as client:
        seed_user()
        for path in DASHBOARD_FEEDS:
            resp = api_get(client, path)
            assert resp.status_code == 200, f"{path} -> {resp.status_code}: {resp.text[:200]}"
            body = resp.json()
            assert isinstance(body, dict), path


def test_batch102_reconciliation_feed_envelope_shape():
    with make_client() as client:
        seed_user()
        resp = api_get(client, "/dashboard/investigation-billing-reconciliation")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Contract fields from InvestigationBillingReconciliationResponse.
        assert "items" in body
        assert "generated_at" in body or "as_of" in body or "summary" in body
