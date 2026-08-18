# HHMS Project State

## Authoritative baseline
- Current working baseline follows HMS27 plus completed Batch 53 Historical Data Access.
- Latest completed functional milestone before this batch: Batch 53 — Historical Data Access + Archive Workspace.
- Current phase: Functional application build and cross-module integration.
- Comprehensive QA/debugging is not the primary phase yet.

## Locked workflow
1. Build functional application code first.
2. Combine logically related functionality into the largest safe batch whenever technically coherent.
3. Audit the actual generated ZIP before issuing any `git add` command.
4. Provide one combined verification/staging command sequence per batch.
5. Keep commit/push separate until GREEN.
6. Fix defects that block the feature being built; defer broad hardening to QA.
7. Do not create duplicate models, services, endpoints, or frontend modules.
8. Clean only confirmed generated/stale/duplicate clutter.
9. Request fresh full-project baselines at major checkpoints or when state cannot be safely reconstructed.

## Data lifecycle policy — LOCKED
- Patient master remains live regardless of encounter age.
- Current operational year remains live.
- Years 2–5 are online, read-only annual archives loaded on demand.
- Years 6–10 are cold archives accessed only when explicitly requested.
- A renewed case in a new operational year is a new live CaseRecord in the same case family and linked to the prior case.
- Actual clinical timestamps remain authoritative.
- Operational year can be calendar year or configurable financial year; default financial-year start is 1 April.
- Archive age is calculated from the configured operational year, not blindly from Gregorian year.
- Generic cleanup never deletes clinical/business data.
- Safe maintenance may remove runtime artifacts, checkpoint WAL, run SQLite optimization and create verified backups.
- VACUUM is administrator-triggered.
- Historical archive databases are not kept attached during normal operation.
- Years beyond the configured cold-retention window are flagged for policy review, not automatically deleted.

## Completed functional areas
- Backend/core, clinical/IPD, billing/MRD, pharmacy/inventory/procurement: substantially complete.
- Statistics/reporting/printing: substantially complete.
- LAN server/client foundation: implemented.
- Administration/RBAC/settings: substantially implemented.
- Audit/service activity: implemented.
- Operational year and case renewal foundation: implemented.
- Historical data access: implemented.
- Archive retention tier planning/access: current batch.

## Current functional focus
- Archive retention tier enforcement.
- Cross-module workflow continuity.
- Remaining operational integrations.
- Server/client packaging and deployment.

## QA boundary
- Comprehensive QA/debugging, performance testing, security testing, recovery testing and release validation begin only after functional code and integration are substantially complete.

## Cleanup policy
- Transfer baselines exclude `.git`, `.env`, Python caches/compiled files, test caches and build artifacts.
- Local `E:\HMS` cleanup may remove only confirmed generated clutter unless explicitly instructed otherwise.
- Do not delete source files based only on filename similarity; confirm references first.
- Historical documentation is retained unless demonstrably obsolete, duplicated or contradicted.
