# Annual Case Rollover

Batch 69 adds the first physical live-to-archive rollover workflow for yearly case records.

## Safety sequence

An administrator requests rollover for a completed operational year. HHMS first creates a
verified SQLite backup named for the pre-rollover operation. The backup is integrity-checked
before the archive snapshot is created.

The archive is a verified, read-only-by-convention SQLite snapshot of the live database at the
rollover point. Its SHA-256 checksum and file metadata are stored in `ArchiveManifest`.

## Live data transition

For the selected operational year, HHMS records permanent `CaseArchiveReference` rows containing
patient, case-family, case-number and original case identity. Direct clinical children of a case
(`Diagnosis` and `FollowUp`) are removed together with the archived `CaseRecord` rows. Any newer
live case that points to an archived case through `renewed_from_case_id` is cleared to avoid a
live foreign-key reference to a physically removed row; the shared `case_family_id` remains the
longitudinal linkage and the archived snapshot retains the original predecessor ID.

Patient master data is not removed. Since Batches 70-76 the same references-before-delete
pattern extends to visits, invoices/payments, dispense records, admissions, investigations and
medical documents, and (Batch 76) purchase orders, goods receipts, stock transactions and
stock-card ledger entries. Master data (Patient, Supplier, Medicine, InventoryItem) and live
StockBatch balance rows are never rolled over; only document/ledger rows with completed-year
lifecycle metadata participate in physical archival.

## Validation

Before commit, HHMS validates the archive file. After the live transaction commits, it confirms
that no `CaseRecord` remains for the rolled-over year and runs SQLite `PRAGMA integrity_check` on
the live database.

The workflow is administrator-only. A verified archive manifest prevents a second rollover of
the same operational year.
