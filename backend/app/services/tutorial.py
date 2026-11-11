"""
Progress through the guided first run.

Each check answers one question about the database: has this hospital done this thing
at least once? Not "did this user do it" - a hospital where the receptionist registered
the patient and the doctor wrote the prescription has completed two steps between them,
and the tutorial should say so.

The checks are deliberately simple. A tutorial that graded the quality of a
prescription would be a tutorial nobody finishes.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tutorial import STEPS
from app.models.invoice import Invoice
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.visit import Visit


async def _exists(db: AsyncSession, model) -> bool:
    result = await db.execute(select(func.count()).select_from(model).limit(1))
    return bool(result.scalar_one())


async def has_patient(db: AsyncSession) -> bool:
    return await _exists(db, Patient)


async def has_visit(db: AsyncSession) -> bool:
    return await _exists(db, Visit)


async def has_prescription(db: AsyncSession) -> bool:
    return await _exists(db, Prescription)


async def has_invoice(db: AsyncSession) -> bool:
    return await _exists(db, Invoice)


async def has_print(db: AsyncSession) -> bool:
    """A prescription that has been printed at least once.

    ``printed_at`` is the record the software keeps of a document leaving the building,
    which is the closest honest answer to "did somebody print something".
    """

    result = await db.execute(
        select(func.count())
        .select_from(Prescription)
        .where(Prescription.printed_at.is_not(None))
    )
    return bool(result.scalar_one())


CHECKS = {
    "has_patient": has_patient,
    "has_visit": has_visit,
    "has_prescription": has_prescription,
    "has_invoice": has_invoice,
    "has_print": has_print,
}


async def progress(db: AsyncSession) -> dict:
    """Every step, with whether it has been done."""

    steps = []
    for step in STEPS:
        done = await CHECKS[step.check](db)
        steps.append(
            {
                "code": step.code,
                "title": step.title,
                "what": step.what,
                "why": step.why,
                "view": step.view,
                "done": done,
            }
        )

    completed = sum(1 for step in steps if step["done"])
    return {
        "steps": steps,
        "completed": completed,
        "total": len(steps),
        "finished": completed == len(steps),
        "note": (
            "A step counts as done when the hospital has done it at least once, "
            "whoever did it. Nothing here looks at which patient you used."
        ),
    }


__all__ = ["CHECKS", "progress"]
