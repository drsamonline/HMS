"""
Granting one person a permission their role does not give them.

The rule that shapes everything here: **you may only grant what you hold.** An
administrator holds the whole catalogue, so in practice they can grant anything. A
manager who has been given ``permissions.manage`` can pass on what they have and nothing
more - which is exactly what delegation should mean, and what stops a tick-box screen
becoming a privilege-escalation tool.

Nothing here removes a permission that a role grants. See the model's docstring.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException
from app.core.permissions import CODES, PERMISSIONS
from app.models.user_permission import UserPermission
from app.services import audit


def _aware(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; every value here was written as UTC."""

    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


async def grants_for(db: AsyncSession, user_id: int) -> list[UserPermission]:
    """Every grant on record for this user, expired or not."""

    rows = await db.execute(
        select(UserPermission)
        .where(UserPermission.user_id == user_id)
        .order_by(UserPermission.code)
    )
    return list(rows.scalars().all())


async def active_codes(db: AsyncSession, user_id: int) -> frozenset[str]:
    """The grants that still count, right now."""

    now = datetime.now(UTC)
    codes = set()
    for grant in await grants_for(db, user_id):
        expires = _aware(grant.expires_at)
        if expires is None or expires > now:
            codes.add(grant.code)
    return frozenset(codes)


async def grant(
    db: AsyncSession,
    *,
    user_id: int,
    code: str,
    granted_by: int | None,
    expires_at: datetime | None = None,
    reason: str | None = None,
    granter_codes: frozenset[str] | None = None,
) -> UserPermission:
    """Give one person one permission.

    ``granter_codes`` is what the person doing the granting holds. When it is supplied,
    a code they do not hold is refused - delegation passes on what you have, never more.
    """

    if code not in CODES:
        raise BusinessRuleException(
            f"{code} is not a permission this software knows. There are {len(CODES)} in "
            "the catalogue; the administration screen lists them by module."
        )

    if granter_codes is not None and code not in granter_codes:
        raise BusinessRuleException(
            f"You do not hold {code}, so you cannot grant it. A permission may only be "
            "passed on by somebody who has it."
        )

    existing = (
        await db.execute(
            select(UserPermission).where(
                UserPermission.user_id == user_id, UserPermission.code == code
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        existing = UserPermission(user_id=user_id, code=code)
        db.add(existing)

    # Set on both paths. Setting them only when a row already existed meant a *new*
    # grant silently ignored its own expiry - which is how a locum's fortnight becomes
    # permanent, and the test caught it.
    existing.expires_at = expires_at
    existing.reason = reason
    existing.granted_by = granted_by
    existing.granted_at = datetime.now(UTC)
    await db.flush()

    await audit.record(
        db,
        activity="user_permission.grant",
        entity_name="UserPermission",
        entity_id=existing.id,
        after={
            "user_id": user_id,
            "code": code,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "reason": reason,
        },
    )
    return existing


async def revoke(
    db: AsyncSession, *, user_id: int, code: str, revoked_by: int | None
) -> bool:
    """Take back a grant. The role's permissions are untouched."""

    result = await db.execute(
        delete(UserPermission).where(
            UserPermission.user_id == user_id, UserPermission.code == code
        )
    )
    await db.flush()

    if result.rowcount:
        await audit.record(
            db,
            activity="user_permission.revoke",
            entity_name="UserPermission",
            entity_id=None,
            before={"user_id": user_id, "code": code, "revoked_by": revoked_by},
        )
    return bool(result.rowcount)


async def set_grants(
    db: AsyncSession,
    *,
    user_id: int,
    codes: set[str],
    granted_by: int | None,
    expires_at: datetime | None = None,
    reason: str | None = None,
    granter_codes: frozenset[str] | None = None,
) -> dict:
    """Make the set of manual grants exactly ``codes``.

    All or nothing: a screen that half-saves leaves somebody with a permission nobody
    meant to give them, and nobody looking.
    """

    unknown = sorted(set(codes) - CODES)
    if unknown:
        raise BusinessRuleException(
            f"Not permissions this software knows: {', '.join(unknown)}."
        )

    if granter_codes is not None:
        beyond = sorted(set(codes) - set(granter_codes))
        if beyond:
            raise BusinessRuleException(
                f"You do not hold {', '.join(beyond)}, so you cannot grant it."
            )

    current = {grant.code for grant in await grants_for(db, user_id)}

    for code in sorted(codes - current):
        await grant(
            db,
            user_id=user_id,
            code=code,
            granted_by=granted_by,
            expires_at=expires_at,
            reason=reason,
            granter_codes=granter_codes,
        )
    for code in sorted(current - codes):
        await revoke(db, user_id=user_id, code=code, revoked_by=granted_by)

    return {
        "granted": sorted(codes),
        "added": sorted(codes - current),
        "removed": sorted(current - codes),
    }


async def effective(db: AsyncSession, user_id: int, role_codes: frozenset[str]) -> dict:
    """What this person can actually do, and where each permission came from.

    The screen needs the second half: a tick box that is already ticked because of the
    role must look different from one ticked by hand, or nobody can tell what removing
    the role would do.
    """

    manual = await active_codes(db, user_id)
    grants = {grant.code: grant for grant in await grants_for(db, user_id)}

    catalogue = []
    for spec in PERMISSIONS:
        from_role = spec.code in role_codes
        from_manual = spec.code in manual
        grant = grants.get(spec.code)

        catalogue.append(
            {
                "code": spec.code,
                "module": spec.module,
                "name": spec.name,
                "description": spec.description,
                "granted": from_role or from_manual,
                "source": "role" if from_role else ("manual" if from_manual else None),
                # A role permission is not removable here - that is what the role is for.
                "removable": from_manual,
                "expires_at": (
                    _aware(grant.expires_at).isoformat()
                    if grant and _aware(grant.expires_at)
                    else None
                ),
                "reason": grant.reason if grant else None,
            }
        )

    return {
        "user_id": user_id,
        "effective": sorted(role_codes | manual),
        "from_role": sorted(role_codes),
        "from_manual": sorted(manual),
        "permissions": catalogue,
        "note": (
            "Manual grants add to the role and never take away from it. To remove what a "
            "role gives, change the role - so the change is visible to everybody it "
            "affects."
        ),
    }


__all__ = [
    "active_codes",
    "effective",
    "grant",
    "grants_for",
    "revoke",
    "set_grants",
]
