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


## Current Client Milestone
- Client Clinical Case Workspace — Batch 09 implemented.
- Narrative case-taking fields remain free text; quick generals and modalities are compact structured data.
- Each modality supports Agg./Amel. plus additional text.
- Empty sections are omitted/null and do not prevent case saving.
