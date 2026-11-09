"""
The NCH duties a record can be checked against.

The National Commission for Homoeopathy's Code of Ethics Regulations 2022 make four
things software-visible, and three of them can be checked from data HHMS already
holds:

* 7(2) - the practitioner's registration number on every prescription and
  certificate. Checked here as: does the practitioner have one at all?
* 31(1) - the reason for a change of treatment, stated at the next consultation.
  Enforced where the follow-up is written, and counted here.
* 36(c) - records of prescriptions and certificates maintained. Counted here as
  follow-ups that carry a decision but no reason, which is the gap that matters.
* 37 - adverse events reported. Counted here as events recorded and not yet
  marked as reported to an authority.

This is a readiness report rather than a block. A hospital that has just installed
the software has no registration numbers yet, and refusing every prescription until
they are typed in would make the product unusable on day one. The report tells the
administrator what to fix; the enforcement happens where it can be enforced.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.followup import FollowUp
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role
from app.services import adverse_events


async def readiness(db: AsyncSession) -> dict:
    """The three checks, each with the records that fail it."""

    clinicians_missing = await _clinicians_without_registration(db)
    followups_without_reason = await _followups_without_reason(db)
    unreported = await adverse_events.unreported_count(db)

    return {
        "prescriber_registration": {
            "requirement": "NCH Code of Ethics 7(2): registration number on every prescription and certificate.",
            "ok": not clinicians_missing,
            "missing_count": len(clinicians_missing),
            "practitioners": clinicians_missing,
        },
        "reason_for_change": {
            "requirement": "NCH Code of Ethics 31(1): the reason for a change of treatment stated at the next consultation.",
            "ok": followups_without_reason == 0,
            "missing_count": followups_without_reason,
        },
        "adverse_event_register": {
            "requirement": "NCH Code of Ethics 37: adverse events to homoeopathic products reported.",
            "ok": unreported == 0,
            "missing_count": unreported,
            "note": (
                "Every recorded event has been reported."
                if unreported == 0
                else "Events recorded and not yet reported to an authority."
            ),
        },
    }


async def _clinicians_without_registration(db: AsyncSession) -> list[dict]:
    rows = await db.execute(
        select(User.id, User.username, User.full_name)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(
            User.is_active.is_(True),
            Role.role_name.in_(("medical officer", "consultant", "doctor")),
            (User.registration_number.is_(None)) | (func.trim(User.registration_number) == ""),
        )
        .distinct()
    )
    return [
        {"id": user_id, "username": username, "full_name": full_name}
        for user_id, username, full_name in rows.all()
    ]


async def _followups_without_reason(db: AsyncSession) -> int:
    """Follow-ups that changed the treatment and did not say why.

    ``decision`` records what was decided. Two of its four values continue the
    same treatment (``wait``, ``repeat``) and two change it (``change_remedy``,
    ``stop_reassess``); only the latter need a reason.
    """

    result = await db.execute(
        select(func.count())
        .select_from(FollowUp)
        .where(
            FollowUp.decision.in_(("change_remedy", "stop_reassess")),
            (FollowUp.reason_for_change.is_(None))
            | (func.trim(FollowUp.reason_for_change) == ""),
        )
    )
    return result.scalar_one()


__all__ = ["readiness"]
