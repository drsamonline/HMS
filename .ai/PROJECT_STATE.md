# HHMS Project State

## Authoritative baseline
- Baseline: HMS27 clean transfer baseline.
- Latest completed functional milestone: Batch 52 — Operational Year Basis.
- Current project phase: Functional application build and cross-module integration.
- Comprehensive QA/debugging has NOT started as the primary phase.

## Locked development workflow
1. Build functional application code first.
2. Combine logically related work into the largest safe batch whenever technically coherent.
3. Audit the actual generated ZIP before issuing any `git add` command.
4. Every batch uses one combined verification/staging command sequence.
5. Keep commit/push separate until GREEN.
6. Fix defects that block the current feature immediately; defer broad hardening to QA.
7. Do not create duplicate models, services, endpoints, or frontend modules.
8. Clean only confirmed generated/stale/duplicate clutter.
9. Use fresh full-project baselines at major checkpoints or when the current tree cannot be reconstructed safely.

## Data lifecycle policy — LOCKED
- Patient master remains live regardless of encounter age.
- Current operational year remains live.
- Years 2–5 are online, read-only annual archives loaded on demand.
- Years 6–10 are cold archives accessed only when explicitly requested.
- A renewed case in a new operational year is a new live CaseRecord in the same case family, linked to the prior case.
- Actual clinical timestamps remain authoritative.
- Operational year may be calendar year or configurable financial year.
- Generic cleanup never deletes clinical/business data.
- Safe maintenance may clean generated runtime artifacts, checkpoint WAL, run SQLite optimization and create verified backups.
- VACUUM is administrator-triggered.
- Historical data is loaded by selected year; the application does not keep all archive databases attached during normal operation.

## Current functional areas
- Backend/core: substantially complete.
- Clinical/IPD: substantially complete.
- Billing/MRD: substantially complete.
- Pharmacy/inventory/procurement: substantially complete.
- Statistics/reporting/printing: substantially complete.
- LAN server foundation: implemented.
- LAN client: substantially implemented.
- Administration/RBAC/settings: substantially implemented.
- Audit/service activity: implemented.
- Operational year and data lifecycle foundation: implemented.

## Remaining before QA
- Complete cross-module workflow continuity.
- Complete remaining operational/admin integrations.
- Finish controlled physical year-rollover/archive migration.
- Complete server/client packaging and deployment workflow.
- Complete final reporting/printing integration.
- Then enter comprehensive QA/debugging, performance/security testing, recovery testing, clean-machine testing and release validation.

## Cleanup policy
- Transfer baselines always exclude `.git`, `.env`, Python caches/compiled files, test caches and build artifacts.
- Local `E:\HMS` cleanup may remove only confirmed generated clutter unless explicitly instructed otherwise.
- Do not delete source files based only on filename similarity; confirm references first.
- Historical documentation is retained unless demonstrably obsolete, duplicated or contradicted.
