"""The navigation manifest, filtered for the caller.

The client asks once, after login, and renders what it is given. Filtering on the
server rather than the client means a user never receives the name of a screen
they cannot open - which the client-side role map could not promise, because it
shipped the whole list to every browser.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.dependencies.modules import enabled_modules
from app.dependencies.permissions import permissions_for_user
from app.modules.navigation import NAV_ITEMS

router = APIRouter(prefix="/navigation", tags=["Navigation"])


class NavItemRead(BaseModel):
    view: str
    label: str
    module: str
    permission: str | None
    group: str


# No permission guard: this returns the caller's own menu, so it needs a login
# and nothing more. Declared in AUTHENTICATED_ONLY_PATHS so default deny allows
# it deliberately rather than by omission.
@router.get("", response_model=list[NavItemRead])
async def get_navigation(
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> list[NavItemRead]:
    """The sidebar this user should see, in order."""

    enabled = await enabled_modules(db)

    try:
        subject = int(str(current_user.get("sub")))
    except (TypeError, ValueError):
        subject = None
    held = await permissions_for_user(db, subject) if subject is not None else frozenset()

    visible: list[NavItemRead] = []
    for item in NAV_ITEMS:
        if item.module not in enabled:
            continue
        if item.permission is not None and item.permission not in held:
            continue
        visible.append(
            NavItemRead(
                view=item.view,
                label=item.label,
                module=item.module,
                permission=item.permission,
                group=item.group,
            )
        )
    return visible


__all__ = ["router"]
