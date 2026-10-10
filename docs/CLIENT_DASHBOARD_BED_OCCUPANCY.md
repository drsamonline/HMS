# Client Dashboard — IPD Bed-Occupancy Continuity

**Status:** Active (Batch 83) · **Module:** Dashboard / IPD · **Audience:** ward staff, clinicians, administrators

## Purpose

Batches 61 (IPD Bed Occupancy Concurrency) and 73 (IPD Annual Lifecycle) made bed state
trustworthy at the source: admission/discharge lock rows transactionally and a partial
unique index guarantees at most one active admission per bed. Batch 83 turns that trusted
state into an actionable dashboard feed so ward occupancy is visible without opening the
IPD module — who occupies each bed, under which admission, for how long, and a direct
handoff into the patient's clinical workspace.

## Backend Contract

### Endpoint

`GET /api/v1/dashboard/bed-occupancy` (`backend/app/api/v1/endpoints/dashboard.py`)

| Parameter | Type | Default | Constraints |
|-----------|------|---------|-------------|
| `limit`   | int  | 200     | 1–500       |

Authenticated access only (`CurrentUserDependency`).

### Selection & reconciliation rules

- Candidate beds: `Bed.is_active = true` **and** `lower(occupancy_status)` in
  `("occupied", "reserved")`, ordered by ward → bed number (stable ward walkthrough).
- Each candidate is reconciled against its **active admission**: `Admission` rows with
  `lower(admission_status)` in `("admitted", "active")` — the same status pair the
  Batch 61 repository guard uses. The Batch 61 partial unique index means at most one
  row matches per bed; recency ordering keeps the newest defensively.
- Enrichment is batched (no N+1): one query for admissions across all candidate bed
  ids, one query for patients across matched admissions.
- **Drift visibility:** a bed flagged occupied/reserved without a matching active
  admission is still returned with `has_active_admission = false` and null admission
  fields, so data issues surface on the dashboard instead of silently disappearing.
- `length_of_stay_days` is derived from `admission_datetime` (naive-UTC normalised for
  SQLite) against the current UTC time, clamped non-negative.

### Response schemas (`backend/app/schemas/dashboard.py`)

`BedOccupancyItem`: `bed_id`, `bed_number`, `ward`, `room_number`, `bed_type`,
`occupancy_status`, `has_active_admission`, `admission_id`, `admission_number`,
`admission_datetime`, `admission_status`, `patient_id`, `patient_name`,
`patient_number`, `length_of_stay_days`.

`BedOccupancyResponse`: `as_of` (aware UTC timestamp), `items`, `occupied_count`
(beds with a reconciled active admission), `total_beds` (listed candidates).

## Frontend Contract

- API wrapper: `getDashboardBedOccupancy(options)` in `frontend/js/api.js`
  (`{ limit }` → query string; returns the parsed response).
- Dashboard panel: **"IPD bed occupancy"** section in `frontend/js/dashboard.js`
  rendered between Outstanding invoices and Recent patients:
  - summary line `"<occupied> of <total> listed bed(s) occupied"`;
  - one card per bed: heading `bed number · ward`; body shows patient name (number),
    admission number and days admitted when reconciled; drift rows show
    *"Marked occupied but no active admission — check IPD records"* and are disabled;
  - reconciled cards navigate to the patients view and dispatch
    `hhms:open-patient-clinical` (same handoff as the due-follow-up panel);
  - fetch failure renders the graceful unavailable-state, mirroring the sibling panels.

## Tests

Contract suite: `backend/tests/test_dashboard_bed_occupancy.py` (5 tests) locking the
endpoint selection/reconciliation logic, schema fields, frontend wrapper/panel wiring,
and the Batch 61 concurrency guarantees this feed relies on. Full backend suite:
**227 passed**.

## Related

- `.ai/PROJECT_STATE.md` — Batch 61, Batch 73, Batch 83
- `docs/CLIENT_DASHBOARD_OUTSTANDING_INVOICES.md` — Batch 82 sibling panel
- `docs/CLIENT_WORKSPACE.md` / `docs/API_SPECIFICATION.md`
