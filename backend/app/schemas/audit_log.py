"""HHMS audit log read schema."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class AuditLogRead(BaseSchema):
    id: int
    user_id: int
    activity: str
    entity_name: str
    entity_id: int | None
    action_timestamp: datetime
    ip_address: str | None
    remarks: str | None


__all__ = ["AuditLogRead"]
