# HHMS Project State

## Authoritative baseline
- Baseline: current GitHub main after Batch 54 Archive Retention Tier Enforcement.
- Latest completed functional milestone: Batch 54 — Archive Retention Tier Enforcement.
- Current milestone: Batch 55 — Unified Patient History.
- Current project phase: Functional application build and cross-module integration.
- Comprehensive QA/debugging has NOT started as the primary phase.

## Locked workflow
1. Build functional application code first.
2. Combine logically related work into the largest safe batch whenever technically coherent.
3. Audit the actual generated ZIP against the intended change set before issuing any `git add` command.
4. Use one combined verification/staging command sequence per batch.
5. Keep commit/push separate until GREEN.
6. Fix defects that block the current feature immediately; defer broad hardening to QA.
7. Do not create duplicate models, services, endpoints, or frontend modules.
8. Clean only confirmed generated/stale/duplicate clutter.
9. Use fresh full-project baselines at major checkpoints or when the current tree cannot be reconstructed safely.

## Data lifecycle — LOCKED
- Patient master remains live regardless of encounter age.
- Current operational year remains live.
- Years 2–5 are online, read-only annual archives loaded on demand.
- Years 6–10 are cold archives accessed only when explicitly requested.
- A renewed case in a new operational year becomes a new live CaseRecord in the same case family and links to the prior case.
- Operational year may be calendar year or configurable financial year.
- Actual clinical timestamps remain authoritative.
- Generic cleanup never deletes clinical/business data.
- Safe maintenance may clean generated runtime artifacts, checkpoint WAL, run SQLite optimization and create verified backups.
- VACUUM is administrator-triggered.

## Batch 55 functional addition
- Patient Timeline can load live patient activity normally.
- Archived case history can be explicitly loaded by selecting a verified historical year.
- Historical records remain read-only through this access path.
- The client does not attach all archive databases during normal operation.
- Existing archive and operational-year APIs remain the source of truth.

## Remaining before QA
- Complete physical live-to-archive rollover migration.
- Complete remaining cross-module workflow continuity.
- Complete server/client packaging and deployment workflow.
- Complete final reporting/printing integration.
- Then comprehensive QA/debugging, performance/security testing, recovery testing, clean-machine testing and release validation.

## Cleanup policy
- Transfer baselines always exclude `.git`, `.env`, Python caches/compiled files, test caches and build artifacts.
- Local `E:\HMS` cleanup removes only confirmed generated clutter unless explicitly instructed otherwise.
- Do not delete source files based only on filename similarity; confirm references first.
- Historical documentation is retained unless demonstrably obsolete, duplicated or contradicted.
