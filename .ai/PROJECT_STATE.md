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
\n- Client Batch 12: wired Clinical and IPD modules into patient workspace and added investigations/laboratory/X-Ray workspace.\n
- Client Billing + MRD Workspace Batch 13 implemented.

- Client Batch 14: integrated hospital statistics and reports/printing workspace.

- Client Print Renderer: HTML/A4 preview, section selection, print CSS and window.print() integration implemented.

- Client print Batch 16: batch case selection and multi-case print preview implemented.

- Client Unified Dashboard & Navigation Batch 17 prepared.

- Client integration milestone: patient Overview now includes a longitudinal timeline from visits, admissions, investigations, billing invoices, and MRD files.

- Client RBAC navigation batch: consumes /auth/me roles/permissions for top-level module visibility.
