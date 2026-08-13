# HHMS Project State
## Current Phase
- LAN Client / Frontend Foundation
## Current Milestone
- Authenticated client and patient workspace
## Completed
- Backend clinical/statistics/reporting
- LAN server packaging/startup/discovery
- Native WebView2 host
- Client connection shell
## Current Task
- Authenticated client session and patient search
## Next Task
- Patient detail/dashboard
- OPD case record workspace
- IPD, investigations, billing, MRD client screens
- Print preview/rendering
- Final integration and QA
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

- Client Patient Workspace batch completed: patient detail, registration, and module navigation foundation.

- Client Clinical Records — Batch 10: case, diagnosis/ICD-11, prescription, and follow-up workspace integrated.

- Client IPD workspace Batch 11 implemented: admissions, available-bed admission creation, IPD assessment, pain, nutrition, diet, progress and discharge integration.
