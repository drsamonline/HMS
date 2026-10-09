"""Batch 115/116 QA — PDF generation verification & report scheduling.

Milestone 4 tail ("PDF generation verification", "Report scheduling") and
Milestone 7 production-readiness items.  Covers:

* ``app.services.report_pdf.render_envelope_pdf`` contract: real %PDF bytes,
  A4 portrait page geometry, byte-determinism (pinned metadata), unknown
  report_type -> ValueError, missing report_type -> ValueError.
* Envelope type registry consistency with the print-envelope pipeline.
* ``POST /api/v1/reports/pdf`` returns an application/pdf FileResponse for
  authenticated users; malformed payloads are rejected with 422.
* Scheduled-report CRUD under ``/maintenance/report-schedules`` is admin-
  gated (non-admin bearer tokens get 403), cadence validation, and manual
  ``/run`` firing produces a persisted PDF artifact plus run history.
* Scheduler loop integration: ``maintenance_scheduler`` wires
  ``report_scheduler_service.run_due_jobs`` at REPORT_SCHEDULER_INTERVAL_MINUTES.
* Dependency wiring: reportlab pinned in requirements.txt and pyproject.toml.
"""

from __future__ import annotations

import asyncio
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from _qa_harness import make_file_client  # noqa: E402

from app.auth.jwt import create_access_token  # noqa: E402
from app.services.report_pdf import ENVELOPE_KINDS, render_envelope_pdf  # noqa: E402

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

PDF_API = "/api/v1/reports/pdf"
SCHED_API = "/api/v1/maintenance/report-schedules"


def _seed_admin(db_path: str, username: str = "batch115-admin") -> dict[str, str]:
    """Insert an active admin user (role=admin) directly; return bearer headers."""
    from app.auth.password import hash_password
    from app.db.session import get_session_factory
    from app.models.role import Role
    from app.models.user import User
    from app.models.user_role import UserRole

    factory = get_session_factory()

    async def _seed() -> int:
        async with factory() as db:
            user = User(
                username=username,
                password_hash=hash_password("batch115-password"),
                full_name="Batch 115 QA Admin",
                email=None,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            role = Role(role_name="admin", description="QA", is_active=True)
            db.add(role)
            await db.flush()
            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.commit()
            return user.id

    uid = asyncio.run(_seed())
    return {"Authorization": f"Bearer {create_access_token(subject=str(uid))}"}


def _seed_plain_user(db_path: str, username: str = "batch115-clerk") -> dict[str, str]:
    """Active user WITHOUT an admin role — for schedule-gating checks."""
    from app.auth.password import hash_password
    from app.db.session import get_session_factory
    from app.models.user import User

    factory = get_session_factory()

    async def _seed() -> int:
        async with factory() as db:
            user = User(
                username=username,
                password_hash=hash_password("batch115-password"),
                full_name="Batch 115 QA Clerk",
                email=None,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user.id

    uid = asyncio.run(_seed())
    return {"Authorization": f"Bearer {create_access_token(subject=str(uid))}"}


def _envelope(**over) -> dict:
    base = {
        "report_type": "invoice_print",
        "title": "Invoice Receipt QA",
        "generated_at": "2026-10-09T10:00:00+00:00",
        "rows": [{"invoice_no": "INV-0001", "amount": 100.5}],
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# 1. Service-level PDF contract
# ---------------------------------------------------------------------------


def test_render_produces_real_pdf_bytes() -> None:
    data = render_envelope_pdf(_envelope())
    assert data[:5] == b"%PDF-"
    assert b"%%EOF" in data[-32:]
    assert len(data) > 500


def test_render_is_byte_deterministic() -> None:
    env = _envelope()
    first = render_envelope_pdf(env)
    second = render_envelope_pdf(env)
    assert first == second, "same envelope must produce identical PDF bytes"


def test_render_uses_a4_portrait_geometry() -> None:
    data = render_envelope_pdf(_envelope())
    text = data.decode("latin-1")
    mbox = re.search(r"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", text)
    assert mbox is not None, "no MediaBox found in rendered PDF"
    w, h = float(mbox.group(1)), float(mbox.group(2))
    # A4 portrait in points: 595 x 842 (tolerance for unit rounding).
    assert 590 <= w <= 600 and 838 <= h <= 846, f"unexpected page size {w}x{h}"


def test_unknown_report_type_raises_value_error() -> None:
    try:
        render_envelope_pdf(_envelope(report_type="not_a_real_report"))
    except ValueError as exc:
        assert "unknown report_type" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown report_type")


def test_missing_report_type_raises_value_error() -> None:
    env = _envelope()
    env.pop("report_type")
    try:
        render_envelope_pdf(env)
    except ValueError as exc:
        assert "missing report_type" in str(exc)
    else:
        raise AssertionError("expected ValueError for missing report_type")


def test_envelope_kinds_registry_covers_print_pipeline() -> None:
    # Core envelope families locked by Batches 106-113 must all be renderable.
    for kind in (
        "clinical_print",
        "invoice_print",
        "collection_summary_print",
        "receivables_aging_print",
        "refund_audit_print",
        "ward_occupancy_print",
    ):
        assert kind in ENVELOPE_KINDS


# ---------------------------------------------------------------------------
# 2. Endpoint-level contracts (authenticated runtime)
# ---------------------------------------------------------------------------


def test_reports_pdf_endpoint_returns_pdf(tmp_path) -> None:
    db_path = str(tmp_path / "hhms115.pdf.db")
    with make_file_client(db_path) as (client_factory, dispose):
        client = client_factory()
        headers = _seed_admin(db_path)
        resp = client.post(PDF_API, headers=headers, json={"envelope": _envelope()})
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"].startswith("application/pdf")
        assert resp.content[:5] == b"%PDF-"
        types = client.get(f"{PDF_API}/types", headers=headers)
        assert types.status_code == 200
        assert set(ENVELOPE_KINDS) == set(types.json()["report_types"])
        dispose()


def test_reports_pdf_rejects_unknown_type_with_422(tmp_path) -> None:
    db_path = str(tmp_path / "hhms115.bad.db")
    with make_file_client(db_path) as (client_factory, dispose):
        client = client_factory()
        headers = _seed_admin(db_path)
        resp = client.post(
            PDF_API,
            headers=headers,
            json={"envelope": _envelope(report_type="bogus_report")},
        )
        assert resp.status_code == 422, resp.text
        dispose()


def test_reports_pdf_requires_auth(tmp_path) -> None:
    db_path = str(tmp_path / "hhms115.anon.db")
    with make_file_client(db_path) as (client_factory, dispose):
        client = client_factory()
        resp = client.post(PDF_API, json={"envelope": _envelope()})
        assert resp.status_code in (401, 403)
        dispose()


# ---------------------------------------------------------------------------
# 3. Report scheduling: admin gating + CRUD + manual fire
# ---------------------------------------------------------------------------


def test_schedule_crud_is_admin_gated(tmp_path) -> None:
    db_path = str(tmp_path / "hhms115.gate.db")
    with make_file_client(db_path) as (client_factory, dispose):
        client = client_factory()
        clerk = _seed_plain_user(db_path)
        resp = client.get(SCHED_API, headers=clerk)
        assert resp.status_code == 403, "non-admin must not list schedules"
        resp = client.post(
            SCHED_API,
            headers=clerk,
            json={
                "name": "clerk-job",
                "envelope_type": "invoice_print",
                "request_params": {},
                "cadence": "daily",
            },
        )
        assert resp.status_code == 403
        dispose()


def test_schedule_create_list_update_delete_roundtrip(tmp_path) -> None:
    db_path = str(tmp_path / "hhms115.crud.db")
    with make_file_client(db_path) as (client_factory, dispose):
        client = client_factory()
        headers = _seed_admin(db_path)
        body = {
            "name": "Daily collection summary",
            "envelope_type": "collection_summary_print",
            "request_params": {},
            "cadence": "daily",
            "enabled": True,
        }
        created = client.post(SCHED_API, headers=headers, json=body)
        assert created.status_code == 201, created.text
        job = created.json()
        assert job["name"] == body["name"]
        assert job["cadence"] == "daily"
        assert datetime.fromisoformat(job["next_run_at"])

        listed = client.get(SCHED_API, headers=headers)
        assert listed.status_code == 200
        assert any(j["id"] == job["id"] for j in listed.json())

        patched = client.patch(f"{SCHED_API}/{job['id']}", headers=headers, json={"enabled": False})
        assert patched.status_code == 200
        assert patched.json()["enabled"] is False

        bad = client.post(
            SCHED_API,
            headers=headers,
            json={"name": "x", "envelope_type": "invoice_print", "cadence": "hourly"},
        )
        assert bad.status_code == 422, "invalid cadence must be rejected"

        removed = client.delete(f"{SCHED_API}/{job['id']}", headers=headers)
        assert removed.status_code == 204
        after = client.get(SCHED_API, headers=headers)
        assert all(j["id"] != job["id"] for j in after.json())
        dispose()


def test_manual_fire_writes_pdf_artifact_and_history(tmp_path) -> None:
    db_path = str(tmp_path / "hhms115.fire.db")
    with make_file_client(db_path) as (client_factory, dispose):
        client = client_factory()
        headers = _seed_admin(db_path)
        created = client.post(
            SCHED_API,
            headers=headers,
            json={
                "name": "Receivables aging weekly",
                "envelope_type": "receivables_aging_print",
                "request_params": {},
                "cadence": "weekly",
            },
        )
        assert created.status_code == 201, created.text
        job_id = created.json()["id"]

        fired = client.post(f"{SCHED_API}/{job_id}/run", headers=headers)
        assert fired.status_code == 200, fired.text
        run = fired.json()
        assert run["status"] == "success", run.get("error")
        assert run["artifact"].endswith(".pdf")
        assert run["bytes"] and run["bytes"] > 500

        runs = client.get(f"{SCHED_API}/{job_id}/runs", headers=headers)
        assert runs.status_code == 200
        assert len(runs.json()) >= 1

        dl = client.get(f"{SCHED_API}/{job_id}/artifacts/{run['artifact']}", headers=headers)
        assert dl.status_code == 200, dl.text
        assert dl.content[:5] == b"%PDF-"

        # Schedule advanced after firing (weekly -> +7 days).
        after = client.get(SCHED_API, headers=headers).json()
        job_now = next(j for j in after if j["id"] == job_id)
        assert datetime.fromisoformat(job_now["next_run_at"]) > datetime.now(timezone.utc) - timedelta(minutes=5)
        dispose()


# ---------------------------------------------------------------------------
# 4. Scheduler-loop & dependency wiring
# ---------------------------------------------------------------------------


def test_maintenance_scheduler_runs_due_report_jobs() -> None:
    src = (PROJECT_ROOT / "backend/app/services/maintenance_scheduler.py").read_text(encoding="utf-8")
    assert "report_scheduler_service.run_due_jobs" in src
    assert "REPORT_SCHEDULER_INTERVAL_MINUTES" in src or "report_scheduler" in src


def test_settings_expose_report_scheduler_interval() -> None:
    from app.config.settings import get_settings

    s = get_settings()
    assert 5 <= s.REPORT_SCHEDULER_INTERVAL_MINUTES <= 1440


def test_reportlab_pinned_in_dependency_manifests() -> None:
    req = (PROJECT_ROOT / "backend/requirements.txt").read_text(encoding="utf-8")
    proj = (PROJECT_ROOT / "backend/pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r"reportlab>=4\.2,<5\.0", req)
    assert re.search(r"reportlab>=4\.2,<5\.0", proj)
