"""HHMS audit-log query service."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogService:
    async def list_recent(
        self, db: AsyncSession, *, user_id: int | None = None,
        entity_name: str | None = None, activity: str | None = None,
        start_datetime: datetime | None = None, end_datetime: datetime | None = None,
        skip: int = 0, limit: int = 100,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.action_timestamp.desc(), AuditLog.id.desc())
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if entity_name:
            stmt = stmt.where(AuditLog.entity_name == entity_name)
        if activity:
            stmt = stmt.where(AuditLog.activity == activity)
        if start_datetime is not None:
            stmt = stmt.where(AuditLog.action_timestamp >= start_datetime)
        if end_datetime is not None:
            stmt = stmt.where(AuditLog.action_timestamp <= end_datetime)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())


audit_log_service = AuditLogService()

__all__ = ["AuditLogService", "audit_log_service"]
