"""HHMS audit log read schema."""

from __future__ import annotations

from datetime import datetime

from app.schemas.base import BaseSchema


class AuditLogRead(BaseSchema):
    """One row of the audit trail, as the review screen shows it.

    ``before_json`` and ``after_json`` are omitted deliberately: they can carry a
    patient's changed fields, and the review list is a summary. The detail view
    and the export carry them.
    """

    id: int
    user_id: int | None
    actor_username: str | None
    actor_role: str | None
    activity: str
    outcome: str
    entity_name: str
    entity_id: int | None
    action_timestamp: datetime
    request_id: str | None
    ip_address: str | None
    reason: str | None
    remarks: str | None


class AuditLogDetail(AuditLogRead):
    """One row with its evidence."""

    before_json: str | None
    after_json: str | None
    user_agent: str | None
    prev_hash: str | None
    row_hash: str | None


__all__ = ["AuditLogDetail", "AuditLogRead"]
