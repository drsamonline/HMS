"""
First-run setup.

The wizard is ten steps, but only three things have to be true for it to be safe:
the state is known, the person using it proved they are at the server, and every
step applied is recorded.

The setup code is generated on demand and shown in the server log. It is stored
hashed, it expires, and it locks out after repeated failures - a six-digit code
guessing surface is small enough that lockout is not optional.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.models.setup_state import SetupState
from app.services import audit

logger = logging.getLogger("hhms.setup")

#: How long a setup code stays valid.
CODE_LIFETIME = timedelta(minutes=60)

#: How many wrong codes before the installation stops answering the wizard.
MAX_CODE_ATTEMPTS = 5

#: The steps, in order. Declared here rather than in the endpoint so the status
#: response and the apply call cannot disagree about what a step is called.
STEPS = (
    "identity",
    "modules",
    "wards",
    "departments",
    "money",
    "numbering",
    "people",
    "data",
    "network",
    "review",
)


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


async def _state(db: AsyncSession) -> SetupState:
    row = (await db.execute(select(SetupState).limit(1))).scalar_one_or_none()
    if row is None:
        row = SetupState(is_complete=False)
        db.add(row)
        await db.flush()
    return row


def _done(row: SetupState) -> list[str]:
    if not row.steps_done:
        return []
    return [step for step in row.steps_done.split(",") if step]


async def status(db: AsyncSession) -> dict:
    """Whether setup is needed, and which steps are behind us.

    Issues a code the first time it is asked on an unfinished installation. The
    code goes to the server log, which is the one channel a LAN user cannot read.
    """

    row = await _state(db)

    if not row.is_complete and row.code_hash is None:
        code = f"{secrets.randbelow(1_000_000):06d}"
        row.code_hash = _hash(code)
        row.code_issued_at = datetime.now(UTC)
        row.code_attempts = 0
        await db.flush()
        logger.warning(
            "HHMS setup code: %s  (enter this in the setup wizard; it expires in %d minutes)",
            code,
            int(CODE_LIFETIME.total_seconds() // 60),
        )

    return {
        "setup_required": not row.is_complete,
        "steps": list(STEPS),
        "completed_steps": _done(row),
        "locked_out": row.code_attempts >= MAX_CODE_ATTEMPTS,
    }


async def unlock(db: AsyncSession, code: str) -> None:
    """Check the setup code. Raises rather than returning a boolean."""

    row = await _state(db)

    if row.is_complete:
        raise BusinessRuleException("This installation is already set up.")

    if row.code_attempts >= MAX_CODE_ATTEMPTS:
        raise BusinessRuleException(
            "Too many wrong setup codes. Restart the server to be issued a new one."
        )

    if not row.code_hash:
        raise BusinessRuleException("Ask the server for a setup code first.")

    issued = row.code_issued_at or datetime.now(UTC)
    if issued.tzinfo is None:
        # SQLite hands back a naive datetime; the value was written as UTC.
        issued = issued.replace(tzinfo=UTC)
    if datetime.now(UTC) - issued > CODE_LIFETIME:
        raise BusinessRuleException("The setup code has expired. Restart the server.")

    if not secrets.compare_digest(_hash(code.strip()), row.code_hash):
        row.code_attempts += 1
        await db.flush()
        remaining = MAX_CODE_ATTEMPTS - row.code_attempts
        raise BusinessRuleException(f"That code is not correct. {remaining} attempts left.")

    row.code_attempts = 0
    await db.flush()


async def mark_step(db: AsyncSession, step: str) -> None:
    """Record that a step has been applied. Idempotent."""

    if step not in STEPS:
        raise ResourceNotFoundException(f"Unknown setup step: {step}")

    row = await _state(db)
    done = _done(row)
    if step not in done:
        done.append(step)
        row.steps_done = ",".join(done)
    await db.flush()


async def complete(db: AsyncSession) -> None:
    """Close setup. Refuses while a mandatory step is missing."""

    row = await _state(db)
    done = set(_done(row))

    # Only the two steps that must be answered before a hospital can work.
    missing = [step for step in ("identity", "people") if step not in done]
    if missing:
        raise BusinessRuleException(
            f"Setup cannot finish yet: {', '.join(missing)} still to do."
        )

    row.is_complete = True
    row.completed_at = datetime.now(UTC)
    row.code_hash = None

    # Closing setup is the moment the installation becomes a hospital's. It is
    # the first entry in a trail that should outlive whoever ran the wizard.
    await audit.record(
        db,
        activity="setup.complete",
        entity_name="SetupState",
        entity_id=row.id,
        before={"is_complete": False},
        after={"is_complete": True, "steps": sorted(done)},
    )
    await db.flush()


async def is_complete(db: AsyncSession) -> bool:
    return (await _state(db)).is_complete


__all__ = [
    "CODE_LIFETIME",
    "MAX_CODE_ATTEMPTS",
    "STEPS",
    "complete",
    "is_complete",
    "mark_step",
    "status",
    "unlock",
]
