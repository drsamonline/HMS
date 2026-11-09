"""HHMS audit-log API.

Reading the trail is privileged: it exposes who did what across the whole
hospital. Until the permission system is enforced on every route (build plan
B14), access here is gated on the roles carried in the token, and the check is
deliberately in one dependency so B14 can swap it for ``require("audit.read")``
without touching a single route.

Every export writes its own audit row. A review that leaves no trace is
indistinguishable from no review.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.dependencies.auth import CurrentUser, CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogDetail, AuditLogRead
from app.services import audit
from app.services.audit_log import audit_log_service

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


#: Roles that may read the trail. Mirrors the client's ALL_ACCESS_ROLES.
AUDIT_READER_ROLES = frozenset(
    {
        "admin",
        "administrator",
        "hospital administrator",
        "super administrator",
        "auditor",
        "medical superintendent",
    }
)


def require_audit_reader(current_user: CurrentUserDependency) -> CurrentUser:
    """Refuse anyone whose token does not carry a role that may read the trail.

    Temporary shape. B14 replaces this with the permission catalogue so that the
    grant is data an administrator can manage rather than a list in the source.
    """

    roles = current_user.get("roles")
    held = {str(role).strip().lower() for role in roles} if isinstance(roles, (list, tuple)) else set()
    if not held & AUDIT_READER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reading the audit trail requires an administrator or auditor role.",
        )
    return current_user


# ``Annotated`` is what makes FastAPI treat this as a dependency rather than
# as the parameter's type - the same shape the codebase already uses for
# ``CurrentUserDependency``.
AuditReader = Annotated[CurrentUser, Depends(require_audit_reader)]


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(
    db: DatabaseSession,
    current_user: AuditReader,
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


@router.get("/export")
async def export_audit_logs(
    db: DatabaseSession,
    current_user: AuditReader,
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


@router.get("/{audit_id}", response_model=AuditLogDetail)
async def get_audit_log(
    audit_id: int,
    db: DatabaseSession,
    current_user: AuditReader,
) -> AuditLogDetail:
    """One entry with its evidence. Declared after ``/export`` so the literal
    path is matched first."""

    row = await db.get(AuditLog, audit_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit entry not found.")
    return row


__all__ = ["AUDIT_READER_ROLES", "require_audit_reader", "router"]
