# HHMS Project State
## Current Phase
- LAN Client / Frontend Foundation
## Current Milestone
- End-to-end clinical workflow integration
## Completed
- Backend clinical/statistics/reporting
- LAN server packaging/startup/discovery
- Native WebView2 host
- Client connection shell
## Current Task
- Link visits, case records, diagnosis, prescriptions, and follow-ups into one clinical encounter workflow
## Next Task
- Clinical workflow continuation and final integration
- Pharmacy/stock transaction UI
- Final packaging, LAN QA, and release testing
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

- Batch 21: client record-level RBAC and navigation integrity implemented; duplicate bootstrap markup removed.

- Client Runtime Resilience Batch 22: session expiry handling and network loss/recovery UX implemented.

- Client Department/Service Master UI: Batch 26 implemented against existing editable master APIs; reporting capability flags remain data-driven.

- End-to-end clinical workflow integration: linked Visit context to Case Record, Diagnosis, Prescription, and Follow-up; prescription listing can now be scoped by Visit.
