# Legal documents — HHMS

Version 1.0 (draft for review) · 09 November 2026

## What is in this set

| File | Who it is for | What it does |
| --- | --- | --- |
| [`PRIVACY.md`](../../PRIVACY.md) | Anyone evaluating or installing HHMS | States what the software stores, where, and that nothing leaves the installation |
| [`DISCLAIMER.md`](../../DISCLAIMER.md) | Clinicians and hospital administrators | Bounds what the software claims: records, not diagnosis |
| [`RETENTION-AND-ERASURE.md`](RETENTION-AND-ERASURE.md) | The hospital, as Data Fiduciary | Maps the archive tiers to the DPDP retention and erasure duties, and states the erasure gap |
| [`DPDP-NOTICE-TEMPLATE.md`](DPDP-NOTICE-TEMPLATE.md) | The hospital | A patient notice with the nine Rule 3 elements, ready to fill in |
| `LEGAL-INDEX.md` (this file) | Review | Evidence for every factual claim, and the questions a lawyer must settle |

The licence and the security policy already exist at the repository root: [`LICENSE`](../../LICENSE) (proprietary EULA) and [`SECURITY.md`](../../SECURITY.md).

## Facts asserted, and their evidence

Every factual sentence in the privacy and retention documents is checkable against this repository. This table is the check.

| Claim | Evidence in the repo |
| --- | --- |
| The database is SQLite, server-owned, at `data/hhms.sqlite3` | `backend/app/config/runtime_paths.py` — `database_path()` |
| Uploads, backups and logs live under `data/` | same file — `uploads_directory()`, `backups_directory()`, `logs_directory()` |
| The data directory can be relocated | same file — `HHMS_APPLICATION_ROOT` |
| Only the server opens the database; clients use HTTP/JSON on the LAN | `README.md`, architecture table |
| No outbound internet connection | a search of the source for external hosts returns only documentation links, `localhost`, `127.0.0.1` and a LAN address. WHO ICD-11 links are documentation references |
| No telemetry, analytics or crash reporting | a search for `sendBeacon`, `telemetry`, `analytics`, `sentry`, `bugsnag` returns nothing |
| Named accounts, roles, permissions, rate-limited sign-in, token sessions | `backend/app/models/user.py`, `role.py`, `permission.py`, `README.md` |
| A permanent audit trail of user activity | `backend/app/models/audit_log.py` — "Permanent record of significant system activities" |
| Rollover verifies with SHA-256 and keeps patient master data | `docs/ANNUAL_CASE_ROLLOVER.md` |
| Tiers: live, 2–5 online, 6–10 cold, older retained; nothing auto-deleted | `docs/ARCHIVE_RETENTION_TIERS.md` |
| Deleting a patient deactivates, and does not erase | `backend/app/api/v1/endpoints/patients.py` — `deactivate_patient` calls `patient_service.deactivate` |
| Health fields held include diagnosis, prescriptions, investigations, admissions | `backend/app/models/` — the model list |

## Statutory basis

- **DPDP Act, 2023** — s.5 notice, s.6 consent, s.7 legitimate uses, s.8 general obligations (s.8(5) safeguards, s.8(6) breach, s.8(7) erasure), s.9 children, ss.11–14 rights, s.16 cross-border, s.33 penalties.
- **DPDP Rules, 2025** — r.3 notice elements, r.6 breach, rr.8–9 retention, rr.10–12 children, r.16 processor terms. Checked against the Act and Rules as compiled in `repo-legal-docs/references/dpdp-2023.md`; **verify against India Code and the eGazette before publication.**
- **SPDI Rules, 2011** (under IT Act s.43A) — health condition and medical records are sensitive personal data; still relevant until the DPDP regime fully displaces them.
- **Copyright Act, 1957** — the EULA's basis.

## Open questions for counsel

1. **Erasure.** Does anonymisation satisfy s.12(3) for a clinical record, or must the record be destroyed? This decides the shape of the feature described in `RETENTION-AND-ERASURE.md`.
2. **Children.** What consent basis applies to a child treated in the ordinary course, outside an emergency (s.9)?
3. **Retention period.** What period does a homoeopathic hospital in Gujarat have to keep clinical records, and under which instrument?
4. **Archives.** On erasure, must a cold archive be rebuilt, or is excluding the person from onward disclosure enough?
5. **Who is the fiduciary in a multi-tenant deployment.** If one hospital group runs HHMS for several units on one server, who is the fiduciary per unit?
6. **Cross-border.** Nothing in the code transfers data abroad, but a hospital may restore a backup to a cloud drive. Is that a transfer under s.16, and what does the hospital have to do?
7. **Development tooling.** `docs/IMPLEMENTATION_RULES.md` lists optional external AI models for code review and bug detection. That is a development-workflow choice, not a runtime feature, and no patient data is involved — but confirm that no such call is reachable from the shipped build before this document is published.

## Review gates before publishing

- Facts: every row in the evidence table re-checked at the commit being released.
- Claims: no "DPDP compliant", no "secure", no clinical claim.
- Consistency: `PRIVACY.md`, `RETENTION-AND-ERASURE.md` and the EULA's clause 5 must agree.
- Professional review: required. This is patient health data in a commercial product.

## Status

Drafts prepared for review on 09 November 2026. They are not legal advice. They describe the software as shipped at this commit, and they are wrong the moment the code changes without them.
