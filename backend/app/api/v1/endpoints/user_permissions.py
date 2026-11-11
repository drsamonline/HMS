"""The tick boxes: giving one person a permission their role does not.

The screen this serves has to answer a question a list of tick boxes does not: *why* is
this one ticked? A permission a role gives and a permission granted by hand look
identical until something goes wrong, and then the difference is the whole
investigation. So every row carries where it came from.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.exceptions import BusinessRuleException
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.dependencies.permissions import permissions_for_user, require
from app.services import user_permissions

router = APIRouter(prefix="/users", tags=["Permissions"])


class GrantWrite(BaseModel):
    codes: list[str]
    expires_at: datetime | None = None
    reason: str | None = None


def _subject(current_user) -> int | None:
    try:
        return int(str(current_user.get("sub")))
    except (TypeError, ValueError):
        return None


@router.get(
    "/{user_id}/permissions",
    dependencies=[Depends(require("roles.manage"))],
)
async def read_user_permissions(user_id: int, db: DatabaseSession) -> dict:
    """Everything this person can do, and where each permission came from."""

    role_codes = await permissions_for_user(db, user_id)
    manual = await user_permissions.active_codes(db, user_id)
    return await user_permissions.effective(db, user_id, role_codes - manual)


@router.put(
    "/{user_id}/permissions",
    dependencies=[Depends(require("roles.manage"))],
)
async def set_user_permissions(
    user_id: int,
    payload: GrantWrite,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> dict:
    """Make the manual grants exactly this set. All or nothing."""

    actor = _subject(current_user)
    granter_codes = await permissions_for_user(db, actor) if actor is not None else frozenset()

    try:
        result = await user_permissions.set_grants(
            db,
            user_id=user_id,
            codes=set(payload.codes),
            granted_by=actor,
            expires_at=payload.expires_at,
            reason=payload.reason,
            granter_codes=granter_codes,
        )
    except BusinessRuleException as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    await db.commit()

    role_codes = await permissions_for_user(db, user_id)
    manual = await user_permissions.active_codes(db, user_id)
    body = await user_permissions.effective(db, user_id, role_codes - manual)
    body["changed"] = result
    return body


__all__ = ["router"]
