"""PDF rendering + report scheduling endpoints (Batch 115/116).

* ``POST /reports/pdf`` — render any print-envelope payload to a PDF.
* ``/reports/schedules`` — CRUD, manual fire, and artifact download for
  recurring scheduled reports (admin-gated, mirroring the maintenance
  surface).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.report_pdf import (
    PdfRenderRequest,
    ReportScheduleCreate,
    ReportScheduleRead,
    ReportScheduleRunRead,
    ReportScheduleUpdate,
)
from app.services.administration import _require_admin
from app.services.report_pdf import ENVELOPE_KINDS, render_envelope_pdf
from app.services.report_scheduler import report_scheduler_service, scheduled_reports_dir

router = APIRouter(prefix="/reports", tags=["Reports"])


def actor_id(user: CurrentUserDependency) -> int:
    return int(str(user["sub"]))


@router.get("/pdf/types")
async def pdf_envelope_types(_: CurrentUserDependency) -> dict:
    """Envelope report types the server can render to PDF."""
    return {"report_types": sorted(ENVELOPE_KINDS)}


@router.post("/pdf")
async def render_pdf(
    payload: PdfRenderRequest, _: CurrentUserDependency
) -> FileResponse:
    """Render a prepared print envelope into an A4 portrait PDF document."""
    try:
        pdf_bytes = render_envelope_pdf(payload.envelope)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return FileResponse(
        None,
        media_type="application/pdf",
        filename="hhms-report.pdf",
        content=pdf_bytes,
    )


# ---------------------------------------------------------------------------
# Scheduled reports (admin-gated)
# ---------------------------------------------------------------------------

schedule_router = APIRouter(prefix="/maintenance/report-schedules", tags=["Maintenance"])


@schedule_router.get("", response_model=list[ReportScheduleRead])
async def list_schedules(db: DatabaseSession, user: CurrentUserDependency):
    await _require_admin(db, actor_id(user))
    return await report_scheduler_service.list_jobs(db)


@schedule_router.post("", response_model=ReportScheduleRead, status_code=status.HTTP_201_CREATED)
async def create_schedule(data: ReportScheduleCreate, db: DatabaseSession, user: CurrentUserDependency):
    await _require_admin(db, actor_id(user))
    try:
        return await report_scheduler_service.create_job(
            db,
            name=data.name,
            envelope_type=data.envelope_type,
            request_params=data.request_params,
            cadence=data.cadence,
            enabled=data.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@schedule_router.patch("/{job_id}", response_model=ReportScheduleRead)
async def update_schedule(job_id: int, data: ReportScheduleUpdate, db: DatabaseSession, user: CurrentUserDependency):
    await _require_admin(db, actor_id(user))
    try:
        return await report_scheduler_service.update_job(db, job_id, data.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@schedule_router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=None)
async def delete_schedule(job_id: int, db: DatabaseSession, user: CurrentUserDependency):
    await _require_admin(db, actor_id(user))
    await report_scheduler_service.delete_job(db, job_id)
    return None


@schedule_router.post("/{job_id}/run", response_model=ReportScheduleRunRead)
async def run_schedule_now(job_id: int, db: DatabaseSession, user: CurrentUserDependency):
    await _require_admin(db, actor_id(user))
    return await report_scheduler_service.fire_job(db, job_id)


@schedule_router.get("/{job_id}/runs", response_model=list[ReportScheduleRunRead])
async def schedule_runs(job_id: int, db: DatabaseSession, user: CurrentUserDependency):
    await _require_admin(db, actor_id(user))
    await report_scheduler_service._get_row(db, job_id)  # 404 if unknown
    return report_scheduler_service.job_runs(job_id)


@schedule_router.get("/{job_id}/artifacts/{name}")
async def download_artifact(job_id: int, name: str, db: DatabaseSession, user: CurrentUserDependency) -> FileResponse:
    await _require_admin(db, actor_id(user))
    await report_scheduler_service._get_row(db, job_id)  # 404 if unknown
    root = scheduled_reports_dir().resolve()
    target = (root / name).resolve()
    if not target.is_file() or root not in target.parents:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artifact not found")
    return FileResponse(target, media_type="application/pdf", filename=name)


__all__ = ["router", "schedule_router"]
