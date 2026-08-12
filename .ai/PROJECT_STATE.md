# HHMS Project State

## Current Phase
- Backend Clinical Activity and Statistics Foundation

## Current Milestone
- Hospital Statistics Engine

## Last Completed Milestone
- Clinical Activity Integration

## Current Task
- Extend statistics with deduplicated department/service demographics and daily reporting

## Next Task
- Reporting/printing backend
- Then LAN packaging and frontend

## Blockers
- None for local clinical record implementation.
- WHO ICD-11 lookup requires optional WHO API credentials.

## Module Status
| Module | Status |
|--------|--------|
| Foundation | Complete |
| Database | Complete |
| Authentication | Complete |
| Patient | Complete |
| OPD / Visits | Complete |
| Prescription | Complete |
| Pharmacy / Inventory | Complete |
| IPD Admission / Bed / Discharge | Complete |
| Laboratory | Complete |
| Billing | Complete |
| Clinical Core | Complete |
| IPD Clinical Documentation | Complete |
| MRD | Complete |
| Frontend | Pending |
| Printing | Pending |
| Reports | Pending |
| Testing / Final Audit | Pending |

## Locked Clinical Design
- One compact CaseRecord for homoeopathic case-taking.
- Narrative sections remain free text.
- Quick-generals and modalities use compact structured data.
- Every modality supports Agg/Amel plus additional text.
- Diagnosis is separate from homoeopathic assessment.
- ICD-11 is optional and searched on demand through the HHMS backend.
- Follow-ups are longitudinal records and do not overwrite the original case.
- Optional/empty clinical sections must never prevent saving or retrieval.

## Last Updated
- 2026-08-12 - Statistics Reporting & Deduplication batch prepared.


## Current Backend Milestone
- Hospital Statistics Engine implemented on the integrated clinical activity sources.


## Statistics Reporting Rules
- Hospital unique-patient totals use distinct patient IDs.
- Department/service demographic counts also use distinct patient IDs.
- Department/service new-old and fulfillment-mode totals represent activity rows.
- Canonical Visit/Admission/Investigation rows are the primary activity sources.
- ServiceActivity projections of canonical records are excluded from aggregate counts.
- Reporting end dates are inclusive.
- Daily breakdown is available in the hospital statistics response.
