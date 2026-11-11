"""
Recording the institution's statutory registrations, and saying which are at risk.

The register answers three questions an inspector asks and a hospital rarely can:
which registrations does this establishment hold, when does each expire, and which of
the ones that apply are missing.

Nothing here decides what the law requires of a particular clinic - that depends on the
state and the premises, and a software product should not pretend to know. It records
what the hospital says applies to it, and reports the gap against that.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException
from app.models.institute_registration import (
    KIND_CODES,
    MANDATORY_BY_DEFAULT,
    REGISTRATION_KINDS,
    InstituteRegistration,
)
from app.services import audit

#: How far ahead to warn. A registration that expires next month is a problem today,
#: because renewing it takes longer than a month.
EXPIRY_WARNING_DAYS = 60


def _aware(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; every value here was written as UTC."""

    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _label(kind: str) -> str:
    return next(label for code, label, _note in REGISTRATION_KINDS if code == kind)


async def upsert(
    db: AsyncSession,
    *,
    kind: str,
    number: str,
    authority: str | None = None,
    issued_on: datetime | None = None,
    valid_until: datetime | None = None,
    applies: bool = True,
    notes: str | None = None,
    recorded_by: int | None = None,
) -> InstituteRegistration:
    """Record or update one registration."""

    if kind not in KIND_CODES:
        raise BusinessRuleException(
            f"{kind} is not a registration this software knows. Known kinds: "
            f"{', '.join(KIND_CODES)}."
        )
    if not number.strip():
        raise BusinessRuleException(f"The {_label(kind)} needs its number.")

    existing = (
        await db.execute(
            select(InstituteRegistration).where(InstituteRegistration.kind == kind)
        )
    ).scalar_one_or_none()

    if existing is None:
        existing = InstituteRegistration(kind=kind)
        db.add(existing)

    before = {
        "number": existing.number,
        "valid_until": existing.valid_until.isoformat() if existing.valid_until else None,
    } if existing.id else None

    existing.number = number.strip()
    existing.authority = authority.strip() if authority else None
    existing.issued_on = issued_on
    existing.valid_until = valid_until
    existing.applies = applies
    existing.notes = notes.strip() if notes else None
    existing.recorded_by = recorded_by

    await db.flush()

    await audit.record(
        db,
        activity="institute_registration.record",
        entity_name="InstituteRegistration",
        entity_id=existing.id,
        before=before,
        after={
            "kind": kind,
            "number": existing.number,
            "valid_until": existing.valid_until.isoformat() if existing.valid_until else None,
            "applies": applies,
        },
    )
    return existing


async def readiness(db: AsyncSession) -> dict:
    """Which registrations apply, which are held, and which need attention."""

    now = datetime.now(UTC)
    horizon = now + timedelta(days=EXPIRY_WARNING_DAYS)

    rows = (
        await db.execute(select(InstituteRegistration))
    ).scalars().all()
    held = {row.kind: row for row in rows}

    entries = []
    for kind, label, note in REGISTRATION_KINDS:
        row = held.get(kind)
        required = kind in MANDATORY_BY_DEFAULT

        expires = _aware(row.valid_until) if row else None
        if row is None:
            state = "not recorded"
        elif expires is not None and expires < now:
            state = "expired"
        elif expires is not None and expires <= horizon:
            state = "expiring"
        else:
            state = "current"

        entries.append(
            {
                "kind": kind,
                "label": label,
                "note": note,
                "required_by_default": required,
                "applies": row.applies if row else required,
                "number": row.number if row else None,
                "authority": row.authority if row else None,
                "valid_until": expires.isoformat() if expires else None,
                "state": state,
            }
        )

    at_risk = [
        entry
        for entry in entries
        if entry["applies"] and entry["state"] in {"expired", "expiring", "not recorded"}
        and (entry["required_by_default"] or entry["number"] is not None)
    ]

    return {
        "registrations": entries,
        "at_risk": at_risk,
        "warning_days": EXPIRY_WARNING_DAYS,
        "note": (
            "Which registrations the law requires depends on the state and the "
            "premises. This records what the establishment says applies to it and "
            "reports the gap against that, rather than deciding for you."
        ),
    }


__all__ = ["EXPIRY_WARNING_DAYS", "readiness", "upsert"]
