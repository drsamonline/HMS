"""
HHMS audit write service.

One place writes audit rows. Endpoints do not call it directly - the service
layer does, because a write made through any other path would leave no trace, and
an audit trail with holes is worse than none: it looks complete.

Transaction rules
-----------------
``record()`` adds the row and flushes. It does **not** commit. The caller commits
once, at the end, so the change and the record of it land together or not at all.
An audit row that survives a rolled-back change is a lie; a change that commits
without its row is a hole. Neither is acceptable, so they share a transaction.

Failure rules
-------------
If the audit row cannot be written, the exception propagates and the caller's
transaction rolls back. That is deliberate: losing an audit row is a failure of
the control, and a control that fails silently is not a control.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import current_request_context
from app.models.audit_log import AuditLog


#: Fields that describe the row rather than the change, so they are not part of
#: a before-and-after comparison. ``id`` is constant; the timestamps move on
#: every write and would make every entry look like a change.
IGNORED_FIELDS = frozenset({"created_at", "updated_at"})

#: Fields covered by the chain hash. Excludes ``id`` because the hash has to be
#: computable before the insert assigns one, and excludes ``prev_hash`` and
#: ``row_hash`` themselves because they are the chain, not the evidence.
HASHED_FIELDS = (
    "user_id",
    "actor_username",
    "actor_role",
    "activity",
    "outcome",
    "entity_name",
    "entity_id",
    "before_json",
    "after_json",
    "reason",
    "action_timestamp",
    "request_id",
    "ip_address",
    "user_agent",
    "remarks",
)


def compute_hash(row: Mapping[str, Any], prev_hash: str | None) -> str:
    """SHA-256 over a row's evidence and the hash of the row before it.

    Any change to a field changes this value; removing a row breaks the link
    that the following row points back to. Together those two properties are what
    turn a silent edit into a detectable one.
    """

    payload = {field: _jsonable(row.get(field)) for field in HASHED_FIELDS}
    payload["prev_hash"] = prev_hash
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def _previous_hash(db: AsyncSession) -> str | None:
    """The row_hash of the newest row, or None for an empty trail."""

    result = await db.execute(
        select(AuditLog.row_hash).order_by(AuditLog.id.desc()).limit(1)
    )
    return result.scalar_one_or_none()


def _jsonable(value: Any) -> Any:
    """Make a column value safe for ``json.dumps`` without losing meaning."""

    if isinstance(value, datetime):
        # Canonical form: UTC, no offset, fixed precision. SQLite hands a naive
        # datetime back on read, so a hash taken over ``isoformat()`` at write
        # time would never match a recomputation at verify time - the chain
        # would report every row as edited. That was a real defect, caught by the
        # first verifier run.
        if value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value.strftime("%Y-%m-%dT%H:%M:%S.%f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def snapshot(instance: Any, fields: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Capture an ORM instance's column values as a plain dictionary.

    Pass ``fields`` to capture only the columns a caller cares about, which
    keeps an audit row about a patient's address from carrying their whole
    medical record.
    """

    source = fields if fields is not None else {
        column.key: getattr(instance, column.key)
        for column in instance.__table__.columns
    }
    return {
        key: _jsonable(value)
        for key, value in source.items()
        if key not in IGNORED_FIELDS
    }


def changed(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return only the fields that differ, as (before, after) pairs.

    Storing the whole row twice would answer "what does this record look like"
    and bury the answer to "what changed". Only the difference is kept.
    """

    before = before or {}
    after = after or {}
    keys = set(before) | set(after)
    changed_before: dict[str, Any] = {}
    changed_after: dict[str, Any] = {}
    for key in keys:
        old = before.get(key)
        new = after.get(key)
        if old != new:
            if key in before:
                changed_before[key] = old
            if key in after:
                changed_after[key] = new
    return changed_before, changed_after


def _actor_fields(actor: Mapping[str, Any] | None) -> tuple[int | None, str | None, str | None]:
    """Resolve the actor id, name and role from a JWT payload.

    The claims are read from the token rather than looked up, because an audit
    entry must say what authority the caller held **when they acted**. A lookup
    would report their roles today, which is a different and less useful fact.
    """

    if not actor:
        # No explicit actor: use the one the authentication dependency bound to
        # this request. Services that take an actor still win, so B08's patient
        # paths keep working unchanged.
        context = current_request_context()
        return (
            context.actor_id,
            context.actor_username,
            context.actor_role,
        )

    raw_id = actor.get("sub")
    try:
        actor_id = int(str(raw_id)) if raw_id is not None else None
    except (TypeError, ValueError):
        actor_id = None

    username = actor.get("username")
    roles = actor.get("roles")
    if isinstance(roles, (list, tuple)):
        role_text = ", ".join(str(role) for role in roles) or None
    else:
        role_text = str(roles) if roles else None

    return actor_id, str(username) if username else None, role_text


async def record(
    db: AsyncSession,
    *,
    actor: Mapping[str, Any] | None = None,
    activity: str,
    entity_name: str,
    entity_id: int | None = None,
    before: Mapping[str, Any] | None = None,
    after: Mapping[str, Any] | None = None,
    reason: str | None = None,
    outcome: str = "success",
    remarks: str | None = None,
) -> AuditLog:
    """Add one audit row to the caller's transaction and flush it.

    Parameters
    ----------
    db : AsyncSession
        The caller's session. This function never commits.

    actor : Mapping | None
        The validated JWT payload. Omit it to use the actor the authentication
        dependency bound to the current request, which is what lets a service
        record without taking an actor parameter. Pass ``None`` explicitly only
        for a system action that has no request behind it.

    activity : str
        What happened, as ``entity.verb`` - ``patient.create``,
        ``invoice.void``. Used for filtering, so keep the vocabulary small.

    entity_name : str
        The ORM table name the action touched.

    entity_id : int | None
        The primary key of the row that changed.

    before, after : Mapping | None
        Field snapshots. Only differing fields are stored.
    """

    actor_id, actor_username, actor_role = _actor_fields(actor)
    context = current_request_context()

    changed_before, changed_after = changed(before, after)

    entry = AuditLog(
        user_id=actor_id,
        actor_username=actor_username,
        actor_role=actor_role,
        activity=activity,
        outcome=outcome,
        entity_name=entity_name,
        entity_id=entity_id,
        before_json=(
            json.dumps(changed_before, sort_keys=True, ensure_ascii=False)
            if changed_before
            else None
        ),
        after_json=(
            json.dumps(changed_after, sort_keys=True, ensure_ascii=False)
            if changed_after
            else None
        ),
        reason=reason,
        action_timestamp=datetime.now(UTC),
        request_id=context.request_id,
        ip_address=context.ip_address,
        user_agent=context.user_agent,
        remarks=remarks,
    )

    # Chain the row before it is inserted: prev_hash links it to the newest row,
    # row_hash commits to its own contents. A row written outside this path has
    # no chain and shows up as a break at the next verifier run.
    entry.prev_hash = await _previous_hash(db)
    entry.row_hash = compute_hash(
        {
            "user_id": entry.user_id,
            "actor_username": entry.actor_username,
            "actor_role": entry.actor_role,
            "activity": entry.activity,
            "outcome": entry.outcome,
            "entity_name": entry.entity_name,
            "entity_id": entry.entity_id,
            "before_json": entry.before_json,
            "after_json": entry.after_json,
            "reason": entry.reason,
            "action_timestamp": entry.action_timestamp,
            "request_id": entry.request_id,
            "ip_address": entry.ip_address,
            "user_agent": entry.user_agent,
            "remarks": entry.remarks,
        },
        entry.prev_hash,
    )

    db.add(entry)
    await db.flush()
    return entry


__all__ = [
    "IGNORED_FIELDS",
    "changed",
    "record",
    "snapshot",
]
