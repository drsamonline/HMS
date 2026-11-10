"""
NABH PSQ.3 — what HHMS can serve, and what it cannot.

PSQ.3 is the chapter that asks a hospital to measure itself: 32 mandatory
organisational indicators and 18 department-specific ones, reported monthly. It is
the largest gap between this product and an assessment, and it is the one most
easily faked.

So this file does not enumerate 32 indicator names. The authoritative list lives in
the NABH standard document, which is not in this repository, and a list written from
memory would be a list a hospital could not rely on. What is here instead is the
honest structure: the families those indicators fall into, the data each family
needs, whether HHMS records it today, and - where it does - the indicator that
already serves it.

The point is that a hospital can see, before buying anything, exactly which numbers
this product can produce and which it would have to collect itself.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Psq3Family:
    """One group of PSQ.3 indicators, and what it would take to report it."""

    code: str
    name: str
    #: The indicators in this family, as they are usually described. Not the NABH
    #: wording - see the module docstring for why.
    indicators: tuple[str, ...]
    #: True when HHMS records enough to compute every indicator in the family.
    data_held: bool
    #: What HHMS would need to record, when it does not hold the data.
    missing_data: str | None
    #: The indicator codes from app.core.indicators that already serve this family.
    served_by: tuple[str, ...] = ()


PSQ3_FAMILIES: tuple[Psq3Family, ...] = (
    Psq3Family(
        code="access",
        name="Access and outpatient activity",
        indicators=("OPD footfall", "new to follow-up ratio", "referral rate"),
        data_held=True,
        missing_data=None,
        served_by=("opd_footfall", "new_vs_followup"),
    ),
    Psq3Family(
        code="inpatient",
        name="Inpatient activity",
        indicators=("admissions", "bed occupancy", "average length of stay"),
        data_held=False,
        missing_data=(
            "Discharge date. Admission carries a status but no discharge timestamp, so "
            "length of stay cannot be computed - only the count of open admissions."
        ),
        served_by=("inpatients_admitted", "bed_occupancy"),
    ),
    Psq3Family(
        code="clinical",
        name="Clinical process",
        indicators=("prescriptions per visit", "investigations reported"),
        data_held=True,
        missing_data=None,
        served_by=("prescriptions_per_visit", "investigations_completed"),
    ),
    Psq3Family(
        code="medication_safety",
        name="Medication safety",
        indicators=("medication errors", "adverse drug events", "look-alike sound-alike incidents"),
        data_held=False,
        missing_data=(
            "An incident register. The pharmacovigilance table records adverse events "
            "to products, which is one indicator in this family, not the family."
        ),
        served_by=("adverse_events_reported",),
    ),
    Psq3Family(
        code="patient_safety",
        name="Patient safety incidents",
        indicators=("patient falls", "pressure ulcers", "sentinel events", "wrong-patient events"),
        data_held=False,
        missing_data="A general incident register with severity, review and closure.",
    ),
    Psq3Family(
        code="infection",
        name="Healthcare-associated infection",
        indicators=("surgical site infection", "ventilator-associated pneumonia",
                    "catheter-associated urinary infection", "bloodstream infection",
                    "hand hygiene compliance"),
        data_held=False,
        missing_data=(
            "An infection surveillance register and device-day denominators. A hospital "
            "with no inpatient devices would report zero, which is not the same as "
            "reporting nothing - and the difference must be recorded, not assumed."
        ),
    ),
    Psq3Family(
        code="outcomes",
        name="Clinical outcomes",
        indicators=("inpatient mortality", "unplanned re-admission", "return to theatre",
                    "discharge against medical advice"),
        data_held=False,
        missing_data="Discharge disposition and a discharge timestamp on Admission.",
    ),
    Psq3Family(
        code="experience",
        name="Patient experience",
        indicators=("patient satisfaction", "complaints received and resolved"),
        data_held=False,
        missing_data="A feedback and complaints register.",
    ),
    Psq3Family(
        code="staff_safety",
        name="Staff safety",
        indicators=("needle-stick and sharps injuries", "staff injury reporting"),
        data_held=False,
        missing_data="A staff incident register, separate from patient incidents.",
    ),
    Psq3Family(
        code="records",
        name="Records and consent",
        indicators=("consent completeness", "medical record completeness", "certificate turnaround"),
        data_held=False,
        missing_data=(
            "A consent register. Certificate issuance is recorded (NCH 7(1)), but not "
            "the consent that should precede a procedure."
        ),
        served_by=("certificates_issued",),
    ),
    Psq3Family(
        code="utilisation",
        name="Theatre and resource utilisation",
        indicators=("theatre utilisation", "cancelled procedures"),
        data_held=False,
        missing_data="A theatre list with planned and actual times.",
    ),
)


def coverage() -> dict:
    """What PSQ.3 reporting this installation could support today."""

    served = [family for family in PSQ3_FAMILIES if family.served_by]
    complete = [family for family in PSQ3_FAMILIES if family.data_held]
    indicator_codes = sorted(
        {code for family in PSQ3_FAMILIES for code in family.served_by}
    )

    return {
        "families_total": len(PSQ3_FAMILIES),
        "families_with_any_data": len(served),
        "families_fully_reportable": len(complete),
        "indicators_live": indicator_codes,
        "families": [
            {
                "code": family.code,
                "name": family.name,
                "indicators": list(family.indicators),
                "data_held": family.data_held,
                "missing_data": family.missing_data,
                "served_by": list(family.served_by),
            }
            for family in PSQ3_FAMILIES
        ],
        "note": (
            "The authoritative list of the 32 mandatory and 18 department-specific "
            "PSQ.3 indicators is in the NABH standard, not in this repository. This "
            "reports coverage by family, which is what can be stated honestly today."
        ),
    }


__all__ = ["PSQ3_FAMILIES", "Psq3Family", "coverage"]
