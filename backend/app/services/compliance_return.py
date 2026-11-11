"""
The monthly return a homoeopathy hospital has to be able to produce.

The NCH Code of Ethics makes four things software-visible, and this gathers them
into one document for a period: who prescribed and under what registration, how often
a change of treatment was justified, what certificates were issued, and what adverse
events were reported.

It is deliberately a document rather than four numbers. A return is something a
hospital files, and filing four separate figures from four screens is how one of them
ends up from the wrong month.

QCI asks a different set of questions - patient experience, complaints, safety
culture - and HHMS holds almost none of that data. Rather than leave the section out,
it is present and marked, so nobody mistakes its absence for a clean result.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.indicators import BY_CODE
from app.services import indicators, nch_compliance

#: The NCH duties that make up the return, with the indicator that measures each.
NCH_RETURN = (
    (
        "registration_number",
        "Prescribers with an NCH registration number",
        "NCH Code of Ethics 7(2)",
        None,
    ),
    (
        "reason_recorded",
        "Changes of treatment with a stated reason",
        "NCH Code of Ethics 31(1)",
        "reason_recorded",
    ),
    (
        "certificates_issued",
        "Medical certificates issued and retained",
        "NCH Code of Ethics 7(1)",
        "certificates_issued",
    ),
    (
        "adverse_events_reported",
        "Adverse events reported to an authority",
        "NCH Code of Ethics 37",
        "adverse_events_reported",
    ),
)

#: What QCI asks that HHMS cannot answer yet, and why. Present rather than omitted.
QCI_GAPS = (
    (
        "patient_satisfaction",
        "Patient satisfaction",
        "No feedback register. Nothing in the record asks a patient how the visit was.",
    ),
    (
        "complaints",
        "Complaints received and resolved",
        "No complaints register, and no closure state to measure resolution against.",
    ),
    (
        "safety_culture",
        "Safety culture survey",
        "No survey instrument. This is a staff questionnaire, not a system record.",
    ),
    (
        "access_waiting",
        "Waiting time to consultation",
        "Visit records a start but not a queue entry, so the wait cannot be measured.",
    ),
)


async def monthly_return(
    db: AsyncSession, start: datetime, end: datetime
) -> dict:
    """One period's NCH return, with the QCI section marked."""

    readiness = await nch_compliance.readiness(db)
    registration = readiness["prescriber_registration"]

    duties = []
    for code, label, standard, indicator_code in NCH_RETURN:
        if code == "registration_number":
            # A count of practitioners, not a ratio: the readiness report already
            # knows who is missing one.
            duties.append(
                {
                    "code": code,
                    "label": label,
                    "standard": standard,
                    "value": registration["missing_count"],
                    "unit": "practitioners without a number",
                    "available": True,
                    "source": "GET /api/v1/compliance/nch-readiness",
                }
            )
            continue

        indicator = BY_CODE[indicator_code]
        value = await indicators.COMPUTERS[indicator_code](db, start, end)
        duties.append(
            {
                "code": code,
                "label": label,
                "standard": standard,
                "value": value,
                "unit": indicator.unit,
                "available": value is not None,
                "source": f"indicator {indicator_code}",
            }
        )

    return {
        "period": {"start": start.date().isoformat(), "end": end.date().isoformat()},
        "title": "NCH monthly return",
        "duties": duties,
        "qci": {
            "supported": False,
            "note": (
                "QCI measures patient experience and safety culture, which this "
                "system does not record. The gaps are listed rather than omitted."
            ),
            "gaps": [
                {"code": code, "name": name, "reason": reason}
                for code, name, reason in QCI_GAPS
            ],
        },
    }


__all__ = ["NCH_RETURN", "QCI_GAPS", "monthly_return"]
