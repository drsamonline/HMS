# Archive Retention Tiers

HHMS retains historical data without deleting clinical/business records.

- Current operational year: live.
- Years 2–5: online, read-only archives loaded on demand.
- Years 6–10: cold archives, promoted out of the online archive directory and accessed only on explicit request.
- Older than 10 years: retained for policy review; HHMS does not automatically delete the data.

The operational year is based on the configured calendar or financial-year basis. Therefore archive age is calculated from the operational-year label, not from the Gregorian calendar year.

Cold promotion is a file relocation of a verified SQLite archive plus a manifest update. No clinical/business records are deleted by the retention operation.
