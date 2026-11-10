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
| Families with **any** data in HHMS | 5 |
| Families **fully** reportable today | 3 |
| Live indicators serving them | 9 |

## The families

| Family | Indicators usually reported | HHMS holds the data? | What is missing |
|---|---|---|---|
| Access and outpatient activity | OPD footfall, new to follow-up, referral rate | **yes** | — |
| Clinical process | Prescriptions per visit, investigations reported | **yes** | — |
| Records and consent | Consent completeness, record completeness, certificate turnaround | partial | A consent register. Certificate issuance is recorded; the consent that should precede a procedure is not |
| Inpatient activity | Admissions, bed occupancy, **average length of stay** | partial | **Discharge date.** `Admission` carries a status but no discharge timestamp, so length of stay cannot be computed — only the count of open admissions |
| Medication safety | Medication errors, adverse drug events, look-alike sound-alike | partial | An incident register. The pharmacovigilance table records adverse events to products, which is **one indicator in this family, not the family** |
| Patient safety incidents | Falls, pressure ulcers, sentinel events, wrong-patient events | **no** | A general incident register with severity, review and closure |
| Healthcare-associated infection | SSI, VAP, CAUTI, bloodstream infection, hand hygiene | **no** | An infection surveillance register and device-day denominators |
| Clinical outcomes | Mortality, unplanned re-admission, return to theatre, DAMA | **no** | Discharge disposition and a discharge timestamp |
| Patient experience | Satisfaction, complaints received and resolved | **no** | A feedback and complaints register |
| Staff safety | Needle-stick and sharps injuries, staff injury reporting | **no** | A staff incident register, separate from patient incidents |
| Theatre utilisation | Theatre utilisation, cancelled procedures | **no** | A theatre list with planned and actual times |

## The one that looks close but is not

**Average length of stay** is the trap. The indicator spine computes admissions and
occupancy today, so it is tempting to add length of stay beside them. It cannot be
computed: `Admission` has an `admission_datetime` and an `admission_status`, and no
discharge timestamp anywhere. A dashboard showing "0.0 days" would be worse than one
showing nothing.

The fix is small — one nullable `discharged_at` on `Admission`, written when the
status changes — and it unlocks four indicators across two families: length of stay,
mortality, re-admission and discharge against medical advice. It is not in this
batch because it changes the clinical model, and the model is frozen until that is
decided deliberately.

## The zero that is not a zero

An infection family with no surveillance register reports **nothing**, not zero. A
hospital with no ventilators has no VAP rate; a hospital that never counted also has
no VAP rate, and the two must not look the same on a report. Every family above with
`data_held: false` is reported as unavailable, with the reason, rather than as a zero.

This is the same rule the indicator spine follows: a ratio with an empty denominator
is `None`, never `0`.

## What would move each family

Ordered by cost, cheapest first.

1. **Discharge timestamp** — one nullable column, one write on status change. Unlocks
   length of stay, mortality, re-admission and DAMA. Largest return for the smallest
   change in the whole document.
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
