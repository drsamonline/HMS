"""
The indicator engine.

One function per indicator, each reading the record the hospital already keeps. The
catalogue says what is counted; this counts it.

The honesty rule that shapes every function here: a ratio with an empty denominator
returns ``None``. "No admissions this month" and "0% of admissions were discharged"
are different statements, and a dashboard that shows the second when it means the
first teaches people to distrust it.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.indicators import BY_CODE, INDICATORS
from app.models.admission import Admission
from app.models.adverse_event import AdverseEvent
from app.models.bed import Bed
from app.models.followup import FollowUp
from app.models.investigation import Investigation
from app.models.investigation_result import InvestigationResult
from app.models.medical_certificate import MedicalCertificate
from app.models.prescription import Prescription
from app.models.visit import Visit

#: The decisions that change a treatment (NCH Code of Ethics 31(1)).
CHANGING_DECISIONS = ("change_remedy", "stop_reassess")


def _ratio(numerator: int, denominator: int) -> float | None:
    """A ratio, or None when there is nothing to divide by."""

    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _percent(numerator: int, denominator: int) -> float | None:
    if not denominator:
        return None
    return round(100 * numerator / denominator, 2)


async def _count(db: AsyncSession, model, start: datetime, end: datetime, column) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(model)
        .where(column >= start, column < end)
    )
    return result.scalar_one()


async def opd_footfall(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    return float(await _count(db, Visit, start, end, Visit.visit_datetime))


async def new_vs_followup(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    rows = await db.execute(
        select(Visit.visit_type, func.count())
        .where(Visit.visit_datetime >= start, Visit.visit_datetime < end)
        .group_by(Visit.visit_type)
    )
    counts = {str(kind).lower(): count for kind, count in rows.all()}
    return _ratio(counts.get("new", 0), counts.get("followup", counts.get("follow-up", 0)))


async def bed_occupancy(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    """Occupancy at the end of the period, not averaged across it."""

    active = (
        await db.execute(
            select(func.count()).select_from(Bed).where(Bed.is_active.is_(True))
        )
    ).scalar_one()
    occupied = (
        await db.execute(
            select(func.count())
            .select_from(Bed)
            .where(Bed.is_active.is_(True), Bed.occupancy_status == "occupied")
        )
    ).scalar_one()
    return _percent(occupied, active)


async def inpatients_admitted(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    return float(await _count(db, Admission, start, end, Admission.admission_datetime))


async def prescriptions_per_visit(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    prescriptions = await _count(
        db, Prescription, start, end, Prescription.prescription_datetime
    )
    visits = await _count(db, Visit, start, end, Visit.visit_datetime)
    return _ratio(prescriptions, visits)


async def adverse_events_reported(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    rows = await db.execute(
        select(AdverseEvent.reported, func.count())
        .where(AdverseEvent.event_datetime >= start, AdverseEvent.event_datetime < end)
        .group_by(AdverseEvent.reported)
    )
    counts = dict(rows.all())
    total = sum(counts.values())
    return _percent(counts.get(True, 0), total)


async def certificates_issued(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    return float(await _count(db, MedicalCertificate, start, end, MedicalCertificate.issued_at))


async def reason_recorded(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    changed = (
        await db.execute(
            select(func.count())
            .select_from(FollowUp)
            .where(
                FollowUp.followup_datetime >= start,
                FollowUp.followup_datetime < end,
                FollowUp.decision.in_(CHANGING_DECISIONS),
            )
        )
    ).scalar_one()
    stated = (
        await db.execute(
            select(func.count())
            .select_from(FollowUp)
            .where(
                FollowUp.followup_datetime >= start,
                FollowUp.followup_datetime < end,
                FollowUp.decision.in_(CHANGING_DECISIONS),
                FollowUp.reason_for_change.is_not(None),
                func.trim(FollowUp.reason_for_change) != "",
            )
        )
    ).scalar_one()
    return _percent(stated, changed)


async def investigations_completed(db: AsyncSession, start: datetime, end: datetime) -> float | None:
    requested = await _count(
        db, Investigation, start, end, Investigation.requested_datetime
    )
    if not requested:
        return None

    reported = (
        await db.execute(
            select(func.count(func.distinct(InvestigationResult.investigation_id)))
            .select_from(InvestigationResult)
            .join(Investigation, Investigation.id == InvestigationResult.investigation_id)
            .where(
                Investigation.requested_datetime >= start,
                Investigation.requested_datetime < end,
            )
        )
    ).scalar_one()
    return _percent(reported, requested)


COMPUTERS = {
    "opd_footfall": opd_footfall,
    "new_vs_followup": new_vs_followup,
    "bed_occupancy": bed_occupancy,
    "inpatients_admitted": inpatients_admitted,
    "prescriptions_per_visit": prescriptions_per_visit,
    "adverse_events_reported": adverse_events_reported,
    "certificates_issued": certificates_issued,
    "reason_recorded": reason_recorded,
    "investigations_completed": investigations_completed,
}


async def compute(db: AsyncSession, code: str, start: datetime, end: datetime) -> dict:
    """One indicator's value for a period, with its definition attached."""

    indicator = BY_CODE[code]
    value = await COMPUTERS[code](db, start, end)
    return {
        "code": indicator.code,
        "name": indicator.name,
        "numerator": indicator.numerator,
        "denominator": indicator.denominator,
        "unit": indicator.unit,
        "standard": indicator.standard,
        "group": indicator.group,
        "value": value,
        # None is not zero: it means there was nothing to divide by.
        "available": value is not None,
    }


def month_periods(end: datetime, months: int) -> list[tuple[datetime, datetime]]:
    """Whole calendar months ending with the month that contains ``end``.

    A trend is read month by month because that is the grain a hospital reports at,
    and because a rolling thirty days makes two adjacent points share most of their
    data - which draws a smooth line that hides every real change.
    """

    periods: list[tuple[datetime, datetime]] = []
    year, month = end.year, end.month
    for _ in range(months):
        first = datetime(year, month, 1, tzinfo=end.tzinfo or UTC)
        if month == 12:
            following = datetime(year + 1, 1, 1, tzinfo=end.tzinfo or UTC)
        else:
            following = datetime(year, month + 1, 1, tzinfo=end.tzinfo or UTC)
        periods.append((first, following))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(periods))


async def series(
    db: AsyncSession, code: str, end: datetime, months: int = 6
) -> list[dict]:
    """One indicator, month by month, oldest first."""

    indicator = BY_CODE[code]
    points = []
    for start, finish in month_periods(end, months):
        value = await COMPUTERS[code](db, start, finish)
        points.append(
            {
                "start": start.date().isoformat(),
                "end": finish.date().isoformat(),
                "value": value,
                "available": value is not None,
            }
        )
    return points


async def compute_all(db: AsyncSession, start: datetime, end: datetime) -> list[dict]:
    return [await compute(db, indicator.code, start, end) for indicator in INDICATORS]


__all__ = ["COMPUTERS", "compute", "compute_all", "month_periods", "series"]
