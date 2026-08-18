# HHMS Project State

## Current phase
Functional application build and integration.

## Latest completed milestone
Batch 50 — OPD clinical handoff.

## New architectural integration
- Annual archive policy: 1 year live, years 2–5 online archive, years 6–10 cold archive.
- Patient master remains live; yearly case records renew into the live database while preserving a stable case family and historical linkage.
- Safe maintenance includes runtime cleanup, WAL checkpoint, SQLite optimize, verified backups and health reporting.
- Historical archives are read-only snapshots loaded on demand; live operational queries must not eagerly attach historical databases.


## Current batch
Batch 48 — operational navigation convergence.

## Scope
- Preserve Inventory, Procurement, Audit/Activity navigation alongside the Backup workspace.
- Restore shared procurement API exports lost when the Backup batch replaced api.js.
- Keep Backup access permission-aware.
- Preserve Patients navigation and global workspace routing.

## Rules
- Complete functional code before comprehensive QA/debug.
- Combine logically related functional work whenever technically safe.
- Audit generated ZIP contents before issuing git add commands.
- Use one combined verification/staging command.
- Keep commit/push separate until GREEN.
- Avoid duplicate models, services, endpoints, or frontend modules.
- Remove only confirmed generated/stale/duplicate clutter.


## Current Functional Batch
- Batch 49: OPD Queue integrated into the global client workspace and RBAC navigation.

## Batch 50
- OPD visit/token creation now opens the patient Clinical Workspace directly.
- Preserves server-authoritative token generation and existing OPD queue behavior.

## Data lifecycle policy (LOCKED)
- Current operational year stays in the live database.
- Patient master remains live regardless of encounter age.
- Years 2–5 are online read-only annual archives and are loaded only on demand.
- Years 6–10 are cold archives and are not opened during normal operations.
- A renewed case for a new year is a new live CaseRecord in the same case family; prior-year case remains historically traceable.
- Safe background maintenance may clean runtime artifacts, checkpoint WAL, run PRAGMA optimize and create a verified backup.
- VACUUM is administrator-triggered.
- Business data is never automatically deleted by generic cleanup.


## Operational year
- Supports calendar-year or configurable financial-year basis.
- Actual timestamps remain authoritative; operational-year label is derived.
- Case renewal and archive boundaries use the configured basis.


## Operational year basis
- HHMS supports Calendar Year or configurable Financial Year.
- Default financial start is 1 April.
- Actual clinical timestamps remain authoritative.
- Case renewal, archive boundaries, and annual reporting derive from the configured operational year.
