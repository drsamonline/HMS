# HHMS Data Lifecycle, Case Renewal & Maintenance

## Locked retention model
- Current operational year: live database.
- Years 2–5: online read-only annual archives.
- Years 6–10: cold archives, loaded only when requested.
- Patient master remains live for identity continuity.
- A case renewed in a new year becomes a new live-year CaseRecord with the same case family.
- Safe maintenance may clean runtime artifacts, checkpoint WAL, run `PRAGMA optimize`, and create a verified backup.
- `VACUUM` is administrator-triggered.
- Generic cleanup never deletes clinical/business data.

## Case renewal workflow
1. Patient master remains live.
2. When the clinical workspace opens for a patient whose latest case year is older than the current operational year, HHMS requests a current-year case.
3. If one does not exist, HHMS creates a new CaseRecord with a new case number, the same `case_family_id`, and `renewed_from_case_id` pointing to the prior case.
4. Longitudinal history fields are carried forward selectively; encounter-specific findings are entered fresh.
5. The renewed case is marked `live` and `is_current_year=true`.

## Archive workflow
1. Annual archive creation is a verified SQLite snapshot.
2. Archive metadata, checksum and storage tier are stored in `ArchiveManifest`.
3. Historical archive databases are opened read-only on demand; the live process does not attach every historical year.
4. The current implementation exposes verified annual snapshots and read-only historical case retrieval. Physical purging of historical transactional rows from the live database remains part of the controlled year-rollover implementation and is never performed by generic cleanup.

## Safe maintenance
- Runtime temporary-file cleanup.
- Rotating-log cleanup.
- WAL passive checkpoint.
- SQLite `PRAGMA optimize`.
- Verified backup creation when the configured backup is stale.
- Live system-health metrics.

## Controlled maintenance
`VACUUM` is administrator-triggered because it can require significant I/O and database locking.
