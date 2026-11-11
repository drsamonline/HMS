"""
Verification of the audit chain.

``services.audit`` writes each row with a hash over its own evidence and the
hash of the row before it. This module walks that chain and reports the first
place it does not reconcile.

What it detects
---------------
* A **removed** row: the following row's ``prev_hash`` no longer matches, or a
  gap in ids appears where a row used to be.
* An **edited** row: its ``row_hash`` no longer matches a recomputation over its
  current contents.
* A row written **outside** the service, which carries no hashes at all.

What it does not detect
-----------------------
An attacker who recomputes every subsequent hash. That is why the chain is
described as tamper-evident rather than tamper-proof, and why the head hash is
worth recording somewhere the attacker cannot reach.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services.audit import compute_hash


@dataclass(frozen=True)
class ChainBreak:
    """The first row that does not reconcile, and why."""

    audit_id: int
    reason: str


@dataclass(frozen=True)
class ChainReport:
    """The result of one verification pass."""

    checked: int
    first_break: ChainBreak | None

    @property
    def is_intact(self) -> bool:
        return self.first_break is None


async def verify(
    db: AsyncSession,
    *,
    start_after_id: int = 0,
    limit: int | None = None,
) -> ChainReport:
    """Walk the chain from ``start_after_id`` and report the first break.

    ``limit`` bounds a nightly pass so a long trail does not hold a transaction
    open; verification continues from ``first_break`` or the last id on the next
    run.
    """

    statement = (
        select(AuditLog)
        .where(AuditLog.id > start_after_id)
        .order_by(AuditLog.id)
    )
    if limit is not None:
        statement = statement.limit(limit)

    rows = list((await db.execute(statement)).scalars().all())

    previous: AuditLog | None = None
    if rows and start_after_id:
        previous = await db.get(AuditLog, start_after_id)

    checked = 0
    for row in rows:
        checked += 1

        if row.row_hash is None:
            return ChainReport(
                checked=checked,
                first_break=ChainBreak(
                    audit_id=row.id,
                    reason="row carries no hash: it was written outside the audit service",
                ),
            )

        expected_prev = previous.row_hash if previous is not None else None
        if row.prev_hash != expected_prev:
            return ChainReport(
                checked=checked,
                first_break=ChainBreak(
                    audit_id=row.id,
                    reason=(
                        "prev_hash does not match the preceding row: a row was "
                        "removed, inserted or reordered before this one"
                    ),
                ),
            )

        recomputed = compute_hash(
            {
                "user_id": row.user_id,
                "actor_username": row.actor_username,
                "actor_role": row.actor_role,
                "activity": row.activity,
                "outcome": row.outcome,
                "entity_name": row.entity_name,
                "entity_id": row.entity_id,
                "before_json": row.before_json,
                "after_json": row.after_json,
                "reason": row.reason,
                "action_timestamp": row.action_timestamp,
                "request_id": row.request_id,
                "ip_address": row.ip_address,
                "user_agent": row.user_agent,
                "remarks": row.remarks,
            },
            row.prev_hash,
        )
        if recomputed != row.row_hash:
            return ChainReport(
                checked=checked,
                first_break=ChainBreak(
                    audit_id=row.id,
                    reason="row_hash does not match its contents: the row was edited",
                ),
            )

        previous = row

    return ChainReport(checked=checked, first_break=None)


async def head_hash(db: AsyncSession) -> str | None:
    """The newest row's hash, for recording outside the database."""

    result = await db.execute(
        select(AuditLog.row_hash).order_by(AuditLog.id.desc()).limit(1)
    )
    return result.scalar_one_or_none()


__all__ = [
    "ChainBreak",
    "ChainReport",
    "head_hash",
    "verify",
]
