# Discharge Audit & OPD Queue Daily Summary (Batch 99)

**Domain:** Dashboard operations track · ward-flow and outpatient-flow continuity
**Status:** Implemented and contract-tested
**Mega-batch note:** first batch delivered under the amended mega-batching
policy (D-008) — two coherent operational feeds in one commit.

## Why this exists

The dashboard already exposes point-in-time state (due follow-ups,
outstanding invoices, IPD bed occupancy from Batch 83, pending
investigations). Two operational gaps remained:

1. **Discharges were never audited.** The live discharge workflow marks an
   admission `discharged` and frees its bed when the discharge record is
   created — but if any step drifts (admission left active, bed left
   occupied), the ward silently accumulates phantom occupancy that the
   Batch 83 feed surfaces only as "no active admission" rows days later.
2. **OPD queue pressure was invisible outside the OPD module.** Clinician
   desks had no way to see today's backlog or the trailing days'
   throughput without opening the token queue itself.

Batch 99 closes both gaps with two read-only dashboard feeds built on the
same guarantees the rest of the continuity track uses: derive from live
rows, never trust stored counters, keep drifted/unusual data visible.

## One implementation, one surface each (print-ready by design)

Both derivations are split into a **pure rollup** plus a **scan entry
point** in `backend/app/api/v1/endpoints/dashboard.py`, so a future print
envelope can reuse the exact same numbers without duplicating logic:

| Helper | Responsibility |
| --- | --- |
| `build_discharge_audit_result(rows, as_of)` | Pure reconciliation over serialised discharge scan rows: `admission_discharged` (status reads `discharged`), `bed_freed` (bed link exists and occupancy reads `available`), `is_reconciled` (both flags), `hours_since_discharge` (whole hours vs `as_of`, never negative, tz-aware-safe). Newest-discharge-first; headlines satisfy `reconciled_count + drift_count == total_discharges`. |
| `build_discharge_audit_scan(db, limit)` | Single joined pass Discharge → Admission → Patient with Bed outer-joined (`discharge_datetime DESC, id DESC`, bounded `limit`) — no N+1. |
| `build_opd_queue_summary_result(rows, as_of)` | Pure per-day rollup over `(queue_date, queue_status, token_count)` tuples. Invariants hold line-for-line: `waiting + in_consultation + completed + cancelled == total_tokens` and `open_token_count == waiting + in_consultation`. Statuses matched case-insensitively; unknown statuses count only toward headline totals so the split never silently swallows tokens. Days ordered newest first. |
| `build_opd_queue_summary_scan(db, limit_days)` | Two grouped passes over live `OPDToken`: newest `limit_days` queue dates, then counts grouped by `queue_date × queue_status` — cheap regardless of token volume. |

## Endpoints

| Surface | Route | Method | Query bounds |
| --- | --- | --- | --- |
| Discharge audit | `/api/v1/dashboard/discharge-audit` | GET | `limit` default 200, `1..500` (same taxonomy as the billing continuity feeds) |
| OPD queue summary | `/api/v1/dashboard/opd-queue-summary` | GET | `limit_days` default 14, `1..90` |

Both require authentication (`CurrentUserDependency`) and return
`as_of` timestamps for freshness display.

## Schemas

`backend/app/schemas/dashboard.py` (all exported in `__all__`):

* `DischargeAuditItem` — discharge identity (`discharge_id`,
  `discharge_number`, `discharge_datetime`, `discharge_status`,
  `discharged_by`), admission lineage (`admission_id`,
  `admission_number`, `admission_status`, `admission_discharged`),
  patient identity (`patient_id`, `patient_name`, `patient_number`),
  bed state (`bed_id`, `bed_number`, `ward`, `bed_occupancy_status`,
  `bed_freed`) plus `hours_since_discharge` and `is_reconciled`.
* `DischargeAuditResponse` — `as_of`, `items`, `total_discharges`,
  `reconciled_count`, `drift_count`.
* `OPDQueueSummaryItem` — `queue_date`, `total_tokens`, `waiting`,
  `in_consultation`, `completed`, `cancelled`, `open_token_count`.
* `OPDQueueSummaryResponse` — `as_of`, `items`, `days_reported`,
  `total_tokens`, `total_open`.

## Frontend wiring

* `frontend/js/api.js`: `getDashboardDischargeAudit(options)` (maps
  `options.limit`) and `getDashboardOPDQueueSummary(options)` (maps
  `options.limitDays`).
* `frontend/js/dashboard.js`: two new panels —
  **"Discharge audit"** (`id="dashboard-discharge-audit"`) renders the
  headline triple (total / reconciled / drifted) and one card per
  discharge; drifted cards carry actionable messages ("Admission still
  active — check IPD records", "Bed still occupied — release it in IPD",
  "No bed link — check admission record") instead of disappearing, and
  every card hands off via `hhms:open-patient-clinical` like the Batch 83
  occupancy feed. **"OPD queue daily summary"**
  (`id="dashboard-opd-queue-summary"`) shows the aggregate line (days ·
  tokens · open) plus one row per queue day with the full status split.
  Both panels degrade to their own empty-state text on request failure.

## Contract tests

`backend/tests/test_dashboard_discharge_audit_opd_queue_summary.py`
locks in: reconciliation flags/headline invariants, ordering, non-negative
ages, tz-aware inputs, the day-total status-split invariant,
case-insensitive statuses, unknown-status handling, empty scans, endpoint
wiring (joined/grouped scans, bounded queries), helper and schema exports,
schema round-trips, frontend wrappers/panels, and documentation indexing.

## Notes & boundaries

* Read-only feeds: no mutation, no new indexes required (both scans ride
  existing FK/date columns).
* A discharge whose admission has no bed link reports `bed_freed=false`
  — deliberately conservative so orphaned rows surface for review.
* Print envelopes for these feeds are natural follow-ups under the
  mega-batching policy and will call the shared helpers above unchanged.
