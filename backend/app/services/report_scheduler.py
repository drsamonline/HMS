"""Report scheduling service — Milestone 5 "report scheduling" (Batch 116).

Admins register recurring report jobs (which print envelope, with what
request parameters, on which cadence).  The scheduler loop ticks hourly and
fires any job whose next run is due.  Each fire renders the envelope through
the Batch 115 PDF engine and writes a timestamped artifact under
``data/scheduled_reports/``, then records the run so the API can expose
last-run status.

Design notes:
* Job definitions persist in the existing ``SystemSetting`` table under the
  ``report_schedule:<id>`` key (JSON payload) — no schema migration needed.
* Runs are kept in-process (bounded history) — durable history belongs to
  the backup pipeline.
* A failing fire never escapes into the loop: the run is recorded as
  ``failed`` with the error text and the schedule still advances.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import ResourceNotFoundException
from app.models.system_setting import SystemSetting
from app.services.report_pdf import ENVELOPE_KINDS, render_envelope_pdf
from app.services.reporting import reporting_service

logger = logging.getLogger("hhms.reports.scheduler")

SETTING_KEY_PREFIX = "report_schedule:"
CADENCES = ("daily", "weekly", "monthly")
MAX_RUN_HISTORY = 50


def scheduled_reports_dir() -> Path:
    root = Path(get_settings().ROOT_DIR) / "data" / "scheduled_reports"
    root.mkdir(parents=True, exist_ok=True)
    return root


class ReportSchedulerService:
    """CRUD + execution for recurring report jobs."""

    def __init__(self) -> None:
        self._runs: dict[int, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------ CRUD

    async def list_jobs(self, db: AsyncSession) -> list[dict[str, Any]]:
        rows = (
            await db.execute(
                select(SystemSetting)
                .where(SystemSetting.setting_key.like(f"{SETTING_KEY_PREFIX}%"))
                .order_by(SystemSetting.setting_key)
            )
        ).scalars().all()
        jobs = []
        for row in rows:
            try:
                job = json.loads(row.setting_value)
            except (TypeError, ValueError):
                continue
            job["last_run"] = self._runs.get(job.get("id"), [])[-1:] or None
            jobs.append(job)
        return jobs

    async def create_job(
        self,
        db: AsyncSession,
        *,
        name: str,
        envelope_type: str,
        request_params: dict[str, Any],
        cadence: str,
        enabled: bool = True,
    ) -> dict[str, Any]:
        if envelope_type not in ENVELOPE_KINDS:
            raise ValueError(f"unknown envelope_type: {envelope_type!r}")
        if cadence not in CADENCES:
            raise ValueError(f"cadence must be one of {CADENCES}")
        existing = await self.list_jobs(db)
        job_id = max((j.get("id", 0) for j in existing), default=0) + 1
        now = datetime.now(timezone.utc)
        job = {
            "id": job_id,
            "name": name.strip(),
            "envelope_type": envelope_type,
            "request_params": request_params or {},
            "cadence": cadence,
            "enabled": enabled,
            "created_at": now.isoformat(),
            "next_run_at": now.isoformat(),
        }
        row = SystemSetting(
            setting_key=f"{SETTING_KEY_PREFIX}{job_id}",
            setting_value=json.dumps(job, sort_keys=True),
            setting_type="json",
            description=f"Scheduled report job: {job['name']}",
            is_editable=False,
        )
        db.add(row)
        await db.commit()
        return job

    async def _get_row(self, db: AsyncSession, job_id: int) -> SystemSetting:
        row = (
            await db.execute(
                select(SystemSetting).where(SystemSetting.setting_key == f"{SETTING_KEY_PREFIX}{job_id}")
            )
        ).scalar_one_or_none()
        if row is None:
            raise ResourceNotFoundException(f"Report schedule {job_id} not found")
        return row

    async def update_job(
        self, db: AsyncSession, job_id: int, patch: dict[str, Any]
    ) -> dict[str, Any]:
        row = await self._get_row(db, job_id)
        job = json.loads(row.setting_value)
        for field in ("name", "cadence", "enabled", "request_params", "envelope_type"):
            if field in patch and patch[field] is not None:
                job[field] = patch[field]
        if job["cadence"] not in CADENCES:
            raise ValueError(f"cadence must be one of {CADENCES}")
        if job["envelope_type"] not in ENVELOPE_KINDS:
            raise ValueError(f"unknown envelope_type: {job['envelope_type']!r}")
        row.setting_value = json.dumps(job, sort_keys=True)
        await db.commit()
        return job

    async def delete_job(self, db: AsyncSession, job_id: int) -> None:
        row = await self._get_row(db, job_id)
        await db.delete(row)
        await db.commit()
        self._runs.pop(job_id, None)

    def job_runs(self, job_id: int) -> list[dict[str, Any]]:
        return list(self._runs.get(job_id, []))

    # ------------------------------------------------------------- execution

    def _advance(self, job: dict[str, Any], from_dt: datetime) -> str:
        delta = {"daily": timedelta(days=1), "weekly": timedelta(days=7), "monthly": timedelta(days=30)}[
            job["cadence"]
        ]
        return (from_dt + delta).isoformat()

    async def run_due_jobs(self, db: AsyncSession, *, now: datetime | None = None) -> list[dict[str, Any]]:
        """Fire every enabled job whose ``next_run_at`` has passed. Returns runs."""
        now = now or datetime.now(timezone.utc)
        runs: list[dict[str, Any]] = []
        for job in await self.list_jobs(db):
            if not job.get("enabled", True):
                continue
            next_raw = job.get("next_run_at")
            if not next_raw:
                continue
            next_at = datetime.fromisoformat(next_raw)
            if next_at > now:
                continue
            run = await self.fire_job(db, job["id"], now=now)
            runs.append(run)
        return runs

    async def fire_job(self, db: AsyncSession, job_id: int, *, now: datetime | None = None) -> dict[str, Any]:
        """Render + persist one job instance; always advances the schedule."""
        now = now or datetime.now(timezone.utc)
        row = await self._get_row(db, job_id)
        job = json.loads(row.setting_value)
        run: dict[str, Any] = {"job_id": job_id, "fired_at": now.isoformat(), "status": "success"}
        try:
            envelope = await self._build_envelope(db, job)
            pdf_bytes = render_envelope_pdf(envelope)
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in job["name"])
            stamp = now.strftime("%Y%m%dT%H%M%SZ")
            artifact = scheduled_reports_dir() / f"{safe_name}_{stamp}.pdf"
            artifact.write_bytes(pdf_bytes)
            run.update({"artifact": artifact.name, "bytes": len(pdf_bytes)})
        except Exception as exc:  # noqa: BLE001 — scheduler must never crash
            logger.exception("Scheduled report %s failed", job_id)
            run.update({"status": "failed", "error": str(exc)})
        finally:
            job["next_run_at"] = self._advance(job, now)
            row.setting_value = json.dumps(job, sort_keys=True)
            await db.commit()
            self._runs.setdefault(job_id, []).append(run)
            self._runs[job_id] = self._runs[job_id][-MAX_RUN_HISTORY:]
        return run

    async def _build_envelope(self, db: AsyncSession, job: dict[str, Any]) -> dict[str, Any]:
        """Dispatch the job's envelope type to the matching reporting builder."""
        etype = job["envelope_type"]
        params = dict(job.get("request_params") or {})
        builders = {
            "invoice_print": "build_invoice_print_envelope",
            "collection_summary_print": "build_collection_summary_print_envelope",
            "receivables_aging_print": "build_receivables_aging_print_envelope",
            "invoice_receipt_continuity_print": "build_invoice_receipt_continuity_print_envelope",
            "receipt_numbering_continuity_print": "build_receipt_numbering_continuity_print_envelope",
            "invoice_payment_reconciliation_print": "build_invoice_payment_reconciliation_print_envelope",
            "payment_method_summary_print": "build_payment_method_summary_print_envelope",
            "payment_method_overpayment_print": "build_payment_method_overpayment_print_envelope",
            "invoice_overpayment_print": "build_invoice_overpayment_print_envelope",
            "invoice_settlement_audit_print": "build_invoice_settlement_audit_print_envelope",
            "refund_audit_print": "build_refund_audit_print_envelope",
            "discharge_audit_print": "build_discharge_audit_print_envelope",
            "opd_queue_summary_print": "build_opd_queue_summary_print_envelope",
            "ward_occupancy_print": "build_ward_occupancy_print_envelope",
            "investigation_billing_reconciliation_print": "build_investigation_billing_reconciliation_print_envelope",
        }
        if etype == "clinical_print":
            raise ValueError("clinical_print requires patient/case context and cannot be scheduled generically")
        method_name = builders.get(etype)
        if method_name is None:
            raise ValueError(f"scheduling not supported for envelope_type {etype!r}")
        builder = getattr(reporting_service, method_name)
        request = self._make_request(etype, params)
        envelope = await builder(db, request)
        return envelope.model_dump(mode="json")

    @staticmethod
    def _make_request(etype: str, params: dict[str, Any]):
        from app.schemas import reporting as R

        mapping = {
            "invoice_print": R.InvoicePrintRequest,
            "collection_summary_print": R.CollectionSummaryPrintRequest,
            "receivables_aging_print": R.ReceivablesAgingPrintRequest,
            "invoice_receipt_continuity_print": R.InvoiceReceiptContinuityPrintRequest,
            "receipt_numbering_continuity_print": R.ReceiptNumberingContinuityPrintRequest,
            "invoice_payment_reconciliation_print": R.InvoicePaymentReconciliationPrintRequest,
            "payment_method_summary_print": R.PaymentMethodSummaryPrintRequest,
            "payment_method_overpayment_print": R.PaymentMethodOverpaymentPrintRequest,
            "invoice_overpayment_print": R.InvoiceOverpaymentPrintRequest,
            "invoice_settlement_audit_print": R.InvoiceSettlementAuditPrintRequest,
            "refund_audit_print": R.RefundAuditPrintRequest,
            "discharge_audit_print": R.DischargeAuditPrintRequest,
            "opd_queue_summary_print": R.OPDQueueSummaryPrintRequest,
            "ward_occupancy_print": R.WardOccupancyPrintRequest,
            "investigation_billing_reconciliation_print": R.InvestigationBillingReconciliationPrintRequest,
        }
        cls = mapping.get(etype)
        if cls is None:
            raise ValueError(f"no request schema for envelope_type {etype!r}")
        return cls(**params)


report_scheduler_service = ReportSchedulerService()

__all__ = ["ReportSchedulerService", "report_scheduler_service", "scheduled_reports_dir", "CADENCES"]
