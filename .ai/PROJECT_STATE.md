# HHMS Project State

## Current Phase
- Client integration, deployment packaging, and final QA

## Current Milestone
- Post-Batch-17 client integration checkpoint

## Completed
- Backend clinical/statistics/reporting
- LAN server packaging/startup/discovery
- Native WebView2 host
- Client connection shell/authentication
- Patient registration/search/workspace
- Homoeopathic clinical case workspace
- Diagnosis / ICD-11 / prescription / follow-up client workspace
- IPD client workspace
- Investigation / laboratory / X-Ray client workspace
- Billing / payments client workspace
- MRD client workspace
- Statistics / reports workspace
- A4 print renderer and section selection
- Date-range and batch case printing
- Unified client dashboard/navigation

## Current Task
- Whole-project cleanup/audit followed by final client integration
- Then LAN packaging verification and end-to-end QA

## Next Tasks
- Complete cross-module client workflow integration
- Role-aware navigation and permissions UI
- Patient longitudinal/timeline experience
- Final report/print QA and real printer testing
- WebView2 runtime packaging verification
- Multi-client LAN testing
- Backup/restore and failure-recovery testing
- Performance/security audit
- Release EXE packaging
- Clean-machine installation test
- Final documentation

## Locked Rules
- Backend owns business logic and database access.
- Client never opens SQLite directly.
- Client-server communication uses LAN HTTP/JSON.
- LAN discovery has manual fallback.
- Frontend uses lightweight HTML/CSS/vanilla JavaScript.
- Native client uses WebView2.
- Optional clinical sections must not block saving.
- Statistics distinguish unique patients from activities.
- Printing uses backend report/print manifests and client rendering.
- Empty clinical blocks must be safe to save, retrieve, print, and ignore when unused.
- Master data such as departments/services must remain editable rather than hard-coded.

## Status Classification
- IMPLEMENTED: production-capable code exists and is integrated.
- FOUNDATION: real working code exists but the wider feature is not yet complete.
- PLANNED: intentionally not implemented yet.
- DOCUMENTATION ONLY: specification or guidance without implementation.

## Working Rules
- Use the newest verified full-project ZIP as the source of truth.
- Do not request a new ZIP after every batch; normally use one after about five commits or a major section.
- Group as many logically related files as safely possible into one ZIP.
- Never call a scaffold complete.
- Avoid duplicate models, services, modules, or speculative abstractions.
- For each batch: verify → stage exact files → staged audit → commit/push.
