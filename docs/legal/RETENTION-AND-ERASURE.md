# Retention and erasure

Version: 1.0 (draft for review)
Effective: on publication
Owner: Dr Sohil Momin — sohilmomin2000@gmail.com
Changes: Initial version.

This document states what HHMS actually does with records over time, what the DPDP Act, 2023 requires, and where the two do not yet meet. It is written from the code and the repository's own design documents, not from an intention.

## What the software does today

Source: `docs/ARCHIVE_RETENTION_TIERS.md`, `docs/ANNUAL_CASE_ROLLOVER.md`, and the archive models in `backend/app/models/`.

| Age of record | Where it lives | Access |
| --- | --- | --- |
| Current operational year | Live database | Normal |
| Years 2–5 | Online archive, read-only | Loaded on demand |
| Years 6–10 | Cold archive, moved out of the online archive directory | Explicit request only |
| Older than 10 years | Retained for policy review | **Not deleted automatically** |

Three properties follow, and each is a deliberate design decision worth stating to a hospital:

1. **Rollover does not delete clinical data.** An annual rollover takes a SHA-256-verified snapshot, records archive references, and moves completed-year document and ledger rows into that snapshot. Nothing is discarded.
2. **Master data is never rolled over.** Patient, Supplier, Medicine, InventoryItem and live stock balances stay in the live database permanently. A patient's identity record therefore persists even when their cases are archived.
3. **Archive age is counted from the operational-year label**, not the Gregorian year, because a hospital may run a financial-year basis.

## What the law requires

- **s.8(7), DPDP Act 2023** — personal data must be erased once the purpose is served and no legal obligation requires retention, unless retention is necessary for a legal purpose.
- **s.12(3)** — a Data Principal may ask for erasure, subject to the same qualification.
- **Rules 8 and 9, DPDP Rules 2025** — retention and erasure practice, including erasure from backups and with processors. Confirm the notified text before relying on the detail.
- **Medical-records retention duties** sit outside the DPDP Act and pull the other way: a hospital is generally expected to keep clinical records for a period set by its regulator and by state rules. The DPDP obligation to erase is qualified by exactly this kind of legal requirement.

The hospital, as Data Fiduciary, must reconcile the two. HHMS gives it the mechanics to do so.

## The gap that needs a decision

**HHMS has no erasure path.** `DELETE /patients/{id}` deactivates a patient — `patient_service.deactivate` — it does not remove or anonymise the record. Deactivation is the right default for a clinical system, because a hospital almost always has a reason to keep the record. But it means that when a Data Principal exercises the right under s.12(3) and no retention obligation applies, there is currently no supported way to honour it.

Three options, in order of preference for a clinical system:

1. **Anonymisation.** Replace identifying fields on the Patient row and its documents with a tombstone, keep the clinical and billing rows intact for statistics and audit. This satisfies erasure of the person while preserving the record's integrity — and it is the option most hospitals will actually accept.
2. **Scoped hard delete.** Remove the patient and their dependent rows where the hospital confirms no retention duty applies, with a mandatory audit-trail entry recording who authorised it and why.
3. **Export-and-purge.** Hand the hospital a complete extract for its own records, then purge. Only where the hospital's own retention duty has expired.

Whichever is chosen, it needs: an audit-trail entry for every erasure, a documented authorisation step, and an entry in this document stating what was removed and what was deliberately kept.

## Erasure and backups

Erasing a row does not erase it from an existing backup. A defensible procedure:

- Erasure applies to the live database immediately.
- Backups age out on the hospital's own schedule, and the hospital records that schedule.
- Where a backup is restored, the erasure is re-applied before the restored database goes back into service.
- Archived snapshots are immutable by design; an erasure that must reach an archive is handled by recording the erasure in the live database and excluding the archived person from onward disclosure, unless the hospital's retention duty has expired and the archive may be rebuilt.

This is a policy for the hospital to adopt, not a feature the software can assume.

## Minimum schedule for a hospital to publish

| Record class | Suggested position | Basis |
| --- | --- | --- |
| Patient identity and clinical case records | Retain for the period the hospital's regulator and state rules require; do not delete earlier | Medical-records duty |
| Billing, invoices, payments | Retain for the statutory financial period, then archive | Tax and accounting law |
| Audit trail | Retain permanently | Accountability; s.8(1) |
| Uploaded documents | Follow the patient record they belong to | — |
| User accounts | Retain while active, and afterwards for the audit trail's integrity | — |
| Backups | Fixed rolling window, stated by the hospital, then destroyed | — |

The periods above are placeholders. A qualified Indian advocate and the hospital's own regulator settle the numbers; the software should then enforce them rather than leaving them to a document.

## What a lawyer must settle

1. The retention period that applies to a homoeopathic hospital's clinical records in the relevant state.
2. Whether anonymisation, rather than deletion, satisfies s.12(3) for this record class.
3. Whether archived snapshots must be rebuilt on erasure, or whether excluding the person from onward disclosure is sufficient.
4. Whether a child's record (s.9) changes any of the above.
