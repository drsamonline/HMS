"""The caller's landing screen.

A receptionist and a medical superintendent opened the same dashboard, which meant
the receptionist scrolled past ward occupancy to reach the patient list, and the
superintendent saw a queue they never work in.

This returns the home for the caller's most senior role, with any panel pointing at
a screen the caller cannot open removed - a shortcut that leads to a refusal is worse
than no shortcut.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.dependencies.modules import enabled_modules
from app.dependencies.permissions import permissions_for_user
from app.models.role import Role
from app.models.user_role import UserRole
from app.modules.homes import home_for
from app.modules.navigation import BY_VIEW

router = APIRouter(prefix="/home", tags=["Home"])


class HomePanelRead(BaseModel):
    kind: str
    title: str
    view: str | None
    source: str | None
    description: str | None


class HomeRead(BaseModel):
    key: str
    title: str
    subtitle: str
    panels: list[HomePanelRead]


async def _role_names(db: DatabaseSession, user_id: int) -> list[str]:
    rows = await db.execute(
        select(Role.role_name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    return [name for (name,) in rows.all()]


# No permission guard: this returns the caller's own landing screen, so it needs a
# login and nothing more. Listed in AUTHENTICATED_ONLY_PATHS so default deny allows
# it deliberately.
@router.get("", response_model=HomeRead)
async def get_home(
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> HomeRead:
    """The landing screen for this account."""

    try:
        subject = int(str(current_user.get("sub")))
    except (TypeError, ValueError):
        subject = None

    roles = await _role_names(db, subject) if subject is not None else []
    home = home_for(roles)

    held = await permissions_for_user(db, subject) if subject is not None else frozenset()
    enabled = await enabled_modules(db)

    panels: list[HomePanelRead] = []
    for panel in home.panels:
        if panel.view is not None:
            item = BY_VIEW.get(panel.view)
            # A shortcut to a screen this hospital does not have, or this account
            # cannot open, would be a button that refuses.
            if item is None or item.module not in enabled:
                continue
            if item.permission is not None and item.permission not in held:
                continue
        panels.append(
            HomePanelRead(
                kind=panel.kind,
                title=panel.title,
                view=panel.view,
                source=panel.source,
                description=panel.description,
            )
        )

    return HomeRead(
        key=home.key, title=home.title, subtitle=home.subtitle, panels=panels
    )


__all__ = ["router"]
