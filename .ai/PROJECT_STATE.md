# HHMS Project State

## Authoritative baseline
- Latest user-supplied full baseline: HMS29.zip.
- Baseline was cleaned before development; functional source and uncommitted source changes were preserved.
- Latest committed functional milestone before this batch: Batch 61 — IPD Bed Occupancy Concurrency.
- Current batch: Batch 62 — API Router Convergence.
- Current phase: Functional build and cross-module integration.
- Comprehensive QA/debugging has NOT started as the primary phase.

## Locked workflow
1. Latest user-supplied full ZIP is the sole authoritative baseline. Do not use remote repositories to reconstruct it unless explicitly requested.
2. Clean every baseline ZIP before development.
3. Build functional code first.
4. Combine related functionality whenever technically safe and coherent.
5. Audit the generated ZIP against the intended change set before any `git add`.
6. GREEN -> commit/push.
7. Broad QA, performance, security, recovery and release validation begin only after functional implementation and packaging are substantially complete.
8. Never delete clinical/business data through generic cleanup.
9. Do not delete source based on filename similarity; verify references first.

## Data lifecycle — LOCKED
- Patient master remains live.
- Current operational year remains live.
- Years 2–5 are online read-only archives.
- Years 6–10 are cold archives accessed on demand.
- New-year case renewal creates a live case linked to the prior case family.
- Operational year may be calendar or configurable financial year.
- Actual clinical timestamps remain authoritative.

## Current functional focus
- Correct API/router integration across implemented modules.
- Cross-module workflow continuity.
- Remaining IPD, laboratory, billing, MRD and deployment workflow gaps.
- Then packaging, comprehensive QA/debugging and release validation.

## Batch 62
- Central API v1 registration is consolidated and ordered by subsystem.
- Previously dangling or omitted routers are explicitly registered: beds, discharges, goods receipts, settings, medical documents, patient history, archive records and operational year.
- This batch corrects integration wiring only; it does not redesign module logic.

## Cleanup policy
- Transfer ZIPs exclude `.git`, `.env`, Python caches/compiled files, test caches, coverage output and build artifacts.
- Local cleanup removes only confirmed generated clutter.

## Batch 63 — API router convergence correction
- Corrects an undefined `administration_router` reference introduced by the prior router convergence change.
- Registers the existing backup, department, dispense, procurement, and stock-batch endpoint routers that were omitted from the prior convergence.
- No endpoint business logic is changed in this correction batch.
