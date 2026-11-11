"""The caller's landing screen.

A receptionist and a medical superintendent opened the same dashboard, which meant the
receptionist scrolled past ward occupancy to reach the patient list, and the
superintendent saw a queue they never work in.

This returns the home for the caller's most senior role, with any panel pointing at a
screen the caller cannot open removed - a shortcut that leads to a refusal is worse than
no shortcut - and any panel that hides when empty removed when it has nothing to say.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.modules.homes import Home, home_for
from app.modules.navigation import BY_VIEW
from app.modules.registry import BY_CODE as MODULE_BY_CODE
from app.dependencies.permissions import permissions_for_user
from app.services import institute_registrations, module_state

router = APIRouter(prefix="/home", tags=["Home"])


async def _registrations_summary(db) -> dict:
    """What the statutory register wants the reader to know, in one line."""

    report = await institute_registrations.readiness(db)
    at_risk = report["at_risk"]
    return {
        "count": len(at_risk),
        "headline": (
            f"{len(at_risk)} statutory registration"
            f"{'' if len(at_risk) == 1 else 's'} need attention"
            if at_risk
            else "Nothing is expiring"
        ),
        "items": [
            {
                "label": entry["label"],
                "state": entry["state"],
                "valid_until": entry["valid_until"],
            }
            for entry in at_risk[:5]
        ],
    }


async def _audit_chain_summary(db) -> dict:
    """Whether the trail still verifies - the one thing it exists to detect."""

    from app.services import audit_chain

    report = await audit_chain.verify(db)
    return {
        "count": 0 if report.is_intact else 1,
        "headline": (
            "The audit trail verifies"
            if report.is_intact
            else f"The audit trail breaks at entry {report.first_break.audit_id}"
        ),
        "items": [] if report.is_intact else [
            {
                "label": "Audit trail",
                "state": "broken",
                "valid_until": None,
            }
        ],
    }


async def _panel_is_empty(panel, db) -> bool:
    """Whether a hide-when-empty panel has nothing to show."""

    if panel.kind == "registrations":
        summary = await _registrations_summary(db)
        return summary["count"] == 0
    if panel.kind == "audit_chain":
        summary = await _audit_chain_summary(db)
        return summary["count"] == 0
    return False


@router.get("")
async def get_home(
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> dict:
    """The landing screen for this user, with the panels they can actually use."""

    enabled = await module_state.enabled_codes(db)

    try:
        subject = int(str(current_user.get("sub")))
    except (TypeError, ValueError):
        subject = None
    held = await permissions_for_user(db, subject) if subject is not None else frozenset()

    roles = await _role_names(db, subject)
    home: Home = home_for(roles)

    panels = []
    for panel in home.panels:
        if panel.view is not None:
            item = BY_VIEW.get(panel.view)
            if item is None or item.module not in enabled:
                continue
            if item.permission is not None and item.permission not in held:
                continue
        if panel.hide_when_empty and await _panel_is_empty(panel, db):
            continue

        entry = {
            "kind": panel.kind,
            "title": panel.title,
            "view": panel.view,
            "description": panel.description,
        }
        if panel.kind == "registrations":
            entry["data"] = await _registrations_summary(db)
        if panel.kind == "audit_chain":
            entry["data"] = await _audit_chain_summary(db)
        panels.append(entry)

    return {
        "key": home.key,
        "title": home.title,
        "subtitle": home.subtitle,
        "roles": roles,
        "panels": panels,
    }


async def _role_names(db, user_id: int | None) -> list[str]:
    """The roles this user holds, by name - what ``home_for`` matches on."""

    from app.models.role import Role
    from app.models.user_role import UserRole

    if user_id is None:
        return []
    result = await db.execute(
        select(Role.role_name).join(UserRole, UserRole.role_id == Role.id).where(
            UserRole.user_id == user_id
        )
    )
    return [name for (name,) in result.all()]


__all__ = ["router"]
