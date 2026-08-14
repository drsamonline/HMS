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

- Batch 21: client record-level RBAC and navigation integrity implemented; duplicate bootstrap markup removed.

- Client Runtime Resilience Batch 22: session expiry handling and network loss/recovery UX implemented.

- Client Department/Service Master UI: Batch 26 implemented against existing editable master APIs; reporting capability flags remain data-driven.

- Client Pharmacy / Dispensing workspace: implemented as next client integration milestone.
\n- Functional build phase: Batch 31 adds client Inventory & Stock Ledger workspace. QA/hardening remains deferred until functional scope is substantially complete.\n
- Client OPD Queue Batch 32: functional front-desk visit registration and token management added.

- Functional build milestone: Client IPD Management workspace — bed census and active admission workflow.

- Batch 36: Client Administration and RBAC management workspace implemented.

- Batch 37: editable staff designation master API and migration implemented; client-ready.

- Current functional build milestone: Hospital/System Settings and Number Sequence client/backend foundation.
- Remaining build focus: complete functional administration/configuration, deeper workflow integration, final packaging, then comprehensive QA/release.

- Functional build Batch 39: client Medicine Master and Medicine Batch management added to Administration/Pharmacy configuration.
