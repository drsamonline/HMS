# HHMS Project State

## Current Phase
- LAN Server/Client Packaging Foundation

## Current Milestone
- Reporting/printing backend completed; next: LAN server packaging foundation

## Last Completed Milestone
- Reporting/Print Manifest Batch 05

## Current Task
- LAN client connection foundation

## Next Task
- LAN client native host packaging
- Then frontend implementation
- Then integration and final audit

## Blockers
- None for local clinical record implementation.
- WHO ICD-11 lookup requires optional WHO API credentials.
- LAN client packaging technology will be implemented after backend reporting/printing is stable.

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
| Statistics | Complete |
| Reporting / Printing | In Progress |
| LAN Server / Client Packaging | In Progress |
| Frontend | Pending |
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

## Locked Deployment Direction
- HHMS is a LAN client/server application.
- Target deployment consists of a server executable and a client executable.
- The server owns the database; clients never access the database file directly.
- Normal operation works without internet access.
- Client discovery should support automatic LAN discovery with manual server-address fallback.
- All required runtime dependencies are packaged with the appropriate executable/deployment bundle.
- The database remains SQLite-first for the portable LAN deployment; PostgreSQL remains compatibility-oriented rather than a production prerequisite.

## Locked Reporting Rules
- Hospital unique-patient totals use distinct patient IDs.
- Department/service demographic counts use distinct patient IDs within that scope.
- Department/service activity totals represent activity rows.
- Canonical Visit/Admission/Investigation rows are primary activity sources.
- ServiceActivity projections of canonical records are excluded from aggregate counts.
- Reporting end dates are inclusive.
- Daily breakdown is available in the hospital statistics response.
- Printing must support entire cases, selected sections/documents, page/document-specific output, date-wise and date-range output, and batch printing where applicable.

## Last Updated
- 2026-08-13 - Reporting/print manifest batch 05 completed.
- 2026-08-13 - LAN server startup hardening started.
- 2026-08-13 - LAN server packaging foundation started.
- 2026-08-13 - LAN server startup hardening completed.
- 2026-08-13 - Native UDP LAN discovery foundation started.
- 2026-08-13 - Fresh HMS(3).zip audited as the new baseline.
- 2026-08-12 - Statistics Reporting & Deduplication Batch 05 completed.
- 2026-08-12 - Statistics reporting dimensions and configurable service-type breakdown completed.

- 2026-08-13 - Lightweight client connection foundation created; native host discovery bridge defined.
