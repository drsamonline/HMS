# Cross-Module Encounter Integrity — Batch 65

The admission, investigation and discharge workflows enforce shared encounter invariants.

- Admission requires an existing patient and a timezone-aware admission timestamp.
- Discharge requires an active admission, a timezone-aware timestamp, and cannot precede admission.
- Investigation requests require a timezone-aware request timestamp and cannot be ordered against a closed admission.
- Existing patient/visit/admission ownership checks remain authoritative.
