"""
The indicator catalogue.

Every number a hospital reports is defined once, here, in words a clinician can
argue with: what is counted, what it is divided by, over what period, and which NABH
element it answers. The engine computes what this declares; nothing computes a
figure that is not declared.

The alternative - a dashboard query per number - is how two screens end up showing
two different occupancies for the same day, and how a hospital discovers the
disagreement in front of an assessor.

Rules this catalogue holds to:

* Every indicator names its numerator and denominator in prose. A ratio whose
  denominator is not stated is a number nobody can check.
* An indicator with no data returns ``None``, never zero. "No admissions this month"
  and "0% of admissions were discharged" are different statements, and only one of
  them is true.
* Nothing here is invented for the dashboard. If the record does not hold the data,
  the indicator is not in the catalogue - it belongs on the roadmap instead.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Indicator:
    """One reportable number."""

    code: str
    name: str
    #: What is counted.
    numerator: str
    #: What it is divided by, or "count" for a plain number.
    denominator: str
    #: What the value means: a count, a percentage, a duration in days.
    unit: str
    #: The NABH element or NCH regulation this answers, where one applies.
    standard: str | None
    #: Which group of the dashboard it belongs to.
    group: str


INDICATORS: tuple[Indicator, ...] = (
    Indicator(
        code="opd_footfall",
        name="OPD footfall",
        numerator="Outpatient visits that started in the period",
        denominator="count",
        unit="visits",
        standard="NABH AAC.5",
        group="activity",
    ),
    Indicator(
        code="new_vs_followup",
        name="New to follow-up ratio",
        numerator="New visits in the period",
        denominator="Follow-up visits in the period",
        unit="ratio",
        standard="NABH AAC.5",
        group="activity",
    ),
    Indicator(
        code="bed_occupancy",
        name="Bed occupancy",
        numerator="Beds occupied at the end of the period",
        denominator="Active beds",
        unit="percent",
        standard="NABH COP.3",
        group="inpatient",
    ),
    Indicator(
        code="inpatients_admitted",
        name="Inpatients admitted",
        numerator="Admissions that started in the period",
        denominator="count",
        unit="admissions",
        standard="NABH COP.1",
        group="inpatient",
    ),
    Indicator(
        code="prescriptions_per_visit",
        name="Prescriptions per visit",
        numerator="Prescriptions issued in the period",
        denominator="Outpatient visits in the period",
        unit="ratio",
        standard="NABH MOM.4",
        group="clinical",
    ),
    Indicator(
        code="adverse_events_reported",
        name="Adverse events reported",
        numerator="Adverse events marked as reported to an authority",
        denominator="Adverse events recorded in the period",
        unit="percent",
        standard="NCH Code of Ethics 37",
        group="safety",
    ),
    Indicator(
        code="certificates_issued",
        name="Certificates issued",
        numerator="Medical certificates issued in the period",
        denominator="count",
        unit="certificates",
        standard="NCH Code of Ethics 7(1)",
        group="records",
    ),
    Indicator(
        code="reason_recorded",
        name="Changes of treatment with a stated reason",
        numerator="Follow-ups that changed the treatment and stated why",
        denominator="Follow-ups that changed the treatment",
        unit="percent",
        standard="NCH Code of Ethics 31(1)",
        group="clinical",
    ),
    Indicator(
        code="average_length_of_stay",
        name="Average length of stay",
        numerator="Days between admission and discharge for episodes discharged in the period",
        denominator="Episodes discharged in the period",
        unit="days",
        standard="NABH COP.3",
        group="inpatient",
    ),
    Indicator(
        code="readmissions_30d",
        name="Unplanned re-admission within 30 days",
        numerator="Admissions to the same patient within 30 days of a discharge",
        denominator="Episodes discharged in the period",
        unit="percent",
        standard="NABH COP.2",
        group="outcomes",
    ),
    Indicator(
        code="inpatient_mortality",
        name="Inpatient mortality",
        numerator="Episodes that ended with the patient's death",
        denominator="Episodes discharged in the period with a recorded outcome",
        unit="percent",
        standard="NABH COP.2",
        group="outcomes",
    ),
    Indicator(
        code="discharge_against_advice",
        name="Discharge against medical advice",
        numerator="Episodes that ended against medical advice",
        denominator="Episodes discharged in the period with a recorded outcome",
        unit="percent",
        standard="NABH COP.2",
        group="outcomes",
    ),
    Indicator(
        code="investigations_completed",
        name="Investigations with a reported result",
        numerator="Investigations in the period that carry a result",
        denominator="Investigations requested in the period",
        unit="percent",
        standard="NABH COP.6",
        group="clinical",
    ),
)

BY_CODE: dict[str, Indicator] = {indicator.code: indicator for indicator in INDICATORS}

#: The order the dashboard shows them in.
GROUPS: tuple[tuple[str, str], ...] = (
    ("activity", "Activity"),
    ("clinical", "Clinical quality"),
    ("inpatient", "Inpatient"),
    ("outcomes", "Outcomes"),
    ("safety", "Safety and reporting"),
    ("records", "Records"),
)

__all__ = ["BY_CODE", "GROUPS", "INDICATORS", "Indicator"]
