# Batch 56 — Corrected Unified Patient History

Batch 55 was committed with an incomplete client-only implementation. Batch 56 corrects that committed feature without rewriting history.

## Functional behavior
- Patient history combines live operational records with explicitly selected verified archive years.
- Archive years are returned through a patient-history endpoint rather than relying on administrator-only archive endpoints.
- Historical case records are read-only in the history view.
- Case renewal relationships (`case_family_id`, `renewed_from_case_id`, `case_year`, `storage_tier`) remain visible.
- All archive loading remains on demand; archive databases are not attached during normal live usage.

## API contract corrections
- Adds `apiPut` required by the operational-year client.
- Fixes the `rawResponse` request option contract.
- Removes a stray literal `\\n` from `api.js`.
