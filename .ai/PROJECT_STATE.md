# HHMS Project State

## Current Phase
- Backend Medical Records

## Current Milestone
- MRD: PatientFile and ArchiveRecord

## Last Completed Milestone
- Billing

## Current Task
- Implement compact MRD patient-file and archive records

## Next Task
- Validate, document, commit Clinical Core
- Then implement frontend clinical workflows

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
| MRD | In Progress |
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
- 2026-08-12 - MRD implementation started.
