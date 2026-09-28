# HHMS Project State

## Authoritative baseline
- Baseline: latest user-supplied full ZIP (`HMS(5).zip`), superseding all older ZIP baselines.
- Latest completed functional milestone: Batch 70 — Encounter Annual Lifecycle & Rollover.
- Current milestone: Batch 71 (next cross-module workflow continuity item).
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

## Batch 69 — Annual Case Rollover
- Added verified pre-rollover backup before annual case archival.
- Added permanent `CaseArchiveReference` records so patient/case identity survives physical live-database removal.
- Added administrator-only rollover preview and execution endpoints plus System Health UI action.
- Rollover physically removes `Diagnosis`, `FollowUp` and `CaseRecord` rows for the selected completed operational year after archive preparation.
- Live `renewed_from_case_id` references are cleared when they would point at a physically archived case; `case_family_id` remains the longitudinal linkage.
- The verified annual archive remains a read-only-by-convention SQLite snapshot and is checksum/integrity validated.
- Other encounter, billing, pharmacy and administrative rows remain live until their own lifecycle metadata and rollover rules are implemented.

## Batch 70 — Encounter Annual Lifecycle & Rollover
- `Visit` now carries lifecycle metadata (`visit_year`, `storage_tier`, `is_current_year`) derived from the encounter date via the operational-year configuration at creation time (migration `0021_visit_operational_year_lifecycle` backfills existing rows).
- Permanent `VisitArchiveReference` records preserve visit identity and archive linkage after physical live-database removal.
- Annual rollover physically removes completed-year `Visit` rows alongside cases: `CaseRecord.visit_id` links are detached first, references are created before deletion, and post-rollover validation confirms no live rows for the rolled-over year remain.
- Archived visits are readable on demand through `/maintenance/archives/{year}/patients/{patient_id}/visits` (client wrapper `getHistoricalArchiveVisits`); historical reads come from the verified annual archive snapshot.
- Rollover preview reports `visit_count` for the target year.

## Remaining before QA
- Extend physical rollover to the remaining lifecycle-managed business data (billing, pharmacy, IPD, laboratory, MRD) as its archival metadata is completed.
- Complete remaining cross-module workflow continuity.
- Complete server/client packaging and deployment workflow.
- Complete final reporting/printing integration.
- Then comprehensive QA/debugging, performance/security testing, recovery testing, clean-machine testing and release validation.

## Cleanup policy
- Transfer baselines always exclude `.git`, `.env`, Python caches/compiled files, test caches and build artifacts.
- Local `E:\HMS` cleanup removes only confirmed generated clutter unless explicitly instructed otherwise.
- Do not delete source files based only on filename similarity; confirm references first.
- Historical documentation is retained unless demonstrably obsolete, duplicated or contradicted.

## Batch 55 correction
- Batch 55 was committed with an incomplete client-only history implementation.
- Batch 56 restores the correct backend history contract and wires the client to it.
- The latest ZIP from the user remains authoritative; remote repository inspection is not used for baseline reconstruction.


## Batch 61 — IPD Bed Occupancy Concurrency
- Admission/discharge now use row locking for the affected bed/admission.
- Database partial unique index prevents more than one active admission per bed.
- Bed allocation/release remains atomic with admission/discharge.

## Batch 66 — Laboratory Result Workflow Completion
- Laboratory results use monotonic status flow: draft -> verified -> released.
- Verified/released reports require result text.
- Released reports are immutable.
- Investigation status advances to in_progress on verification and completed on release.

## Batch 64 — Pharmacy Dispensing Ledger Completion
- Dispensing now creates a corresponding `StockCard` ISSUE/`DISPENSE` entry in the same transaction as stock decrement and `DispenseRecord`.
- Expired StockBatch records are blocked from dispensing at the service layer.
- Stock-batch status endpoint exposes available/expiring/expired/exhausted states for client workflows.

## Batch 68 — Billing Atomic Consistency
- Payment creation locks the invoice row while checking and recording the outstanding balance.
- Invoice payment status is derived from payment totals and is no longer directly client-controlled through invoice update.
- Invoice items cannot be added/removed on paid or cancelled invoices.
- Item add/remove recalculates invoice total and preserves a derived unpaid/partial/paid status.
- Item deletion is blocked if the resulting invoice total would fall below the amount already paid.
