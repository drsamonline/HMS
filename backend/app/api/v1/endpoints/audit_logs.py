"""HHMS audit-log API."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.audit_log import AuditLogRead
from app.services.audit_log import audit_log_service

router = APIRouter(prefix="/audit-logs", tags=["Audit"] )


def actor_id(current_user: CurrentUserDependency) -> int:
    return int(str(current_user["sub"]))


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(
    db: DatabaseSession, current_user: CurrentUserDependency,
    user_id: int | None = Query(default=None, gt=0),
    entity_name: str | None = None, activity: str | None = None,
    start_datetime: datetime | None = None, end_datetime: datetime | None = None,
    skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200),
) -> list[AuditLogRead]:
    # The endpoint intentionally exposes read-only audit data. Authorization remains
    # server-side; the actor is resolved here so future role checks have one boundary.
    _ = actor_id(current_user)
    return await audit_log_service.list_recent(
        db, user_id=user_id, entity_name=entity_name, activity=activity,
        start_datetime=start_datetime, end_datetime=end_datetime, skip=skip, limit=limit,
    )


__all__ = ["router"]
