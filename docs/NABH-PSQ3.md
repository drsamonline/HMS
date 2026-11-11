# NABH PSQ.3 — what HHMS can measure, and what it cannot

PSQ.3 is the chapter that asks a hospital to measure itself: 32 mandatory
organisational indicators and 18 department-specific ones, reported monthly. It is
the largest gap between this product and an assessment.

This document does not list 32 indicator names. **The authoritative list lives in the
NABH standard document, which is not in this repository**, and a list written from
memory would be one a hospital could not rely on. What follows is the honest
structure: the families those indicators fall into, the data each needs, whether HHMS
records it today, and — where it does — the indicator that already serves it.

The machine-readable version of this is `backend/app/core/psq3.py`, served at
`GET /api/v1/indicators/psq3`, so the product reports its own coverage rather than
leaving a hospital to discover it.

---

## Summary

| | Count |
|---|---|
| Families PSQ.3 covers | 11 |
| Families with **any** data in HHMS | 6 |
| Families **fully** reportable today | 3 |
| Live indicators serving them | 12 |

## The families

| Family | Indicators usually reported | HHMS holds the data? | What is missing |
|---|---|---|---|
| Access and outpatient activity | OPD footfall, new to follow-up, referral rate | **yes** | — |
| Clinical process | Prescriptions per visit, investigations reported | **yes** | — |
| Records and consent | Consent completeness, record completeness, certificate turnaround | partial | A consent register. Certificate issuance is recorded; the consent that should precede a procedure is not |
| Inpatient activity | Admissions, bed occupancy, average length of stay | **yes** | — |
| Medication safety | Medication errors, adverse drug events, look-alike sound-alike | partial | An incident register. The pharmacovigilance table records adverse events to products, which is **one indicator in this family, not the family** |
| Patient safety incidents | Falls, pressure ulcers, sentinel events, wrong-patient events | **no** | A general incident register with severity, review and closure |
| Healthcare-associated infection | SSI, VAP, CAUTI, bloodstream infection, hand hygiene | **no** | An infection surveillance register and device-day denominators |
| Clinical outcomes | Mortality, unplanned re-admission, return to theatre, DAMA | partial | Mortality and DAMA are computable since `Discharge.discharge_outcome` was added; **return to theatre** still needs a theatre list |
| Patient experience | Satisfaction, complaints received and resolved | **no** | A feedback and complaints register |
| Staff safety | Needle-stick and sharps injuries, staff injury reporting | **no** | A staff incident register, separate from patient incidents |
| Theatre utilisation | Theatre utilisation, cancelled procedures | **no** | A theatre list with planned and actual times |

## A correction, and what it taught

The first version of this document said length of stay could not be computed because
there was no discharge timestamp anywhere. **That was wrong.** `Admission` has no
discharge timestamp, but a separate `Discharge` table does — with
`discharge_datetime`, written by the discharge service. The data was there; the
assessment had looked in one place.

Length of stay and thirty-day re-admission are now computed from that join, with no
schema change at all.

What genuinely was missing is the **outcome**. `Discharge.discharge_status` answers
whether the record is valid (`discharged` or `cancelled`), not what happened to the
patient. Mortality and discharge against medical advice therefore had no denominator
that meant anything.

`Discharge.discharge_outcome` now records `routine`, `expired`, `against_advice` or
`transferred`. It is nullable and existing rows are left null: an episode nobody
classified has an unknown outcome, not a good one, and the mortality denominator
counts only episodes with a recorded outcome — so mortality cannot fall simply
because record-keeping got worse.

The lesson is recorded rather than tidied away: a gap analysis that names one table
and not its siblings will report a gap that is not there.

## The zero that is not a zero

An infection family with no surveillance register reports **nothing**, not zero. A
hospital with no ventilators has no VAP rate; a hospital that never counted also has
no VAP rate, and the two must not look the same on a report. Every family above with
`data_held: false` is reported as unavailable, with the reason, rather than as a zero.

This is the same rule the indicator spine follows: a ratio with an empty denominator
is `None`, never `0`.

## What would move each family

Ordered by cost, cheapest first.

1. ~~**Discharge timestamp**~~ — done. The timestamp already existed on `Discharge`;
   what was added is the outcome, which unlocked mortality and DAMA. Length of stay
   and re-admission came free once the right table was read.
2. **Incident register** — one table with patient or staff, category, severity,
   review and closure. Unlocks three families: patient safety, staff safety and the
   rest of medication safety.
3. **Consent register** — one table linked to procedure. Unlocks records and consent.
4. **Feedback and complaints register** — one table. Unlocks patient experience.
5. **Infection surveillance** — the only one that needs denominators (device-days),
   so it needs a daily census, not just an event table. Most expensive.
6. **Theatre list** — planned against actual times. Unlocks utilisation.

## What this means for a sales conversation

A hospital can be told, today and without exaggeration: HHMS produces nine indicators
across three complete PSQ.3 families, and tells you honestly which of the remaining
eight it cannot yet support and why. That is a better position than a dashboard of
32 numbers whose definitions nobody can check.
