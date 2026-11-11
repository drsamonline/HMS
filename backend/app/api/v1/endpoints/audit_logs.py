"""HHMS audit-log API.

Reading the trail is privileged: it exposes who did what across the whole
hospital. Access is the ``audit.read`` permission, and export is ``audit.export``
- separated because taking a copy out of the building is a different act from
looking at it.

Every export writes its own audit row. A review that leaves no trace is
indistinguishable from no review.
"""

from __future__ import annotations

from datetime import datetime

from app.dependencies.permissions import require
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogDetail, AuditLogRead
from app.services import audit
from app.services.audit_log import audit_log_service

router = APIRouter(prefix="/audit-logs", tags=["Audit"])




@router.get("", response_model=list[AuditLogRead], dependencies=[Depends(require("audit.read"))])
async def list_audit_logs(
    db: DatabaseSession,
    current_user: CurrentUserDependency,
    user_id: int | None = Query(default=None, gt=0),
    entity_name: str | None = Query(default=None, max_length=100),
    activity: str | None = Query(default=None, max_length=100),
    outcome: str | None = Query(default=None, max_length=20),
    start_datetime: datetime | None = None,
    end_datetime: datetime | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[AuditLogRead]:
    return await audit_log_service.list_recent(
        db,
        user_id=user_id,
        entity_name=entity_name,
        activity=activity,
        outcome=outcome,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        skip=skip,
        limit=limit,
    )


@router.get("/export", dependencies=[Depends(require("audit.export"))])
async def export_audit_logs(
    db: DatabaseSession,
    current_user: CurrentUserDependency,
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    user_id: int | None = Query(default=None, gt=0),
    entity_name: str | None = Query(default=None, max_length=100),
    activity: str | None = Query(default=None, max_length=100),
    outcome: str | None = Query(default=None, max_length=20),
    start_datetime: datetime | None = None,
    end_datetime: datetime | None = None,
) -> Response:
    rows = await audit_log_service.export_rows(
        db,
        user_id=user_id,
        entity_name=entity_name,
        activity=activity,
        outcome=outcome,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )

    # The export is an act on the trail, so it goes in the trail. Committed on
    # its own because the response has already been decided by this point.
    await audit.record(
        db,
        actor=current_user,
        activity="audit.export",
        entity_name="AuditLog",
        entity_id=None,
        reason=f"{len(rows)} row(s) exported as {format}",
    )
    await db.commit()

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if format == "csv":
        return Response(
            content=audit_log_service.to_csv(rows),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="hhms-audit-{stamp}.csv"'
            },
        )
    return Response(
        content=audit_log_service.to_pdf(rows),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="hhms-audit-{stamp}.pdf"'
        },
    )


@router.get("/{audit_id}", response_model=AuditLogDetail, dependencies=[Depends(require("audit.read"))])
async def get_audit_log(
    audit_id: int,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> AuditLogDetail:
    """One entry with its evidence. Declared after ``/export`` so the literal
    path is matched first."""

    row = await db.get(AuditLog, audit_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit entry not found.")
    return row


__all__ = ["router"]
