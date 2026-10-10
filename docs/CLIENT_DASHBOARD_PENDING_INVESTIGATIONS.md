# Client Dashboard — Laboratory Pending-Investigation Feed

**Status:** Active (Batch 84) · **Module:** Dashboard / Laboratory · **Audience:** laboratory staff, clinicians, administrators

## Purpose

Batch 66 (Laboratory Result Workflow Completion) made investigation order state
trustworthy at the source: entering a result moves a `pending` order to
`in_progress`, and releasing a report flips the order to `completed`, while
cancelled orders are frozen. Batch 84 turns that trusted state into an
actionable dashboard feed so the laboratory backlog is visible without opening
the Investigations module — which orders still owe results, for which patient,
under which OPD/IPD encounter, and how long each has been waiting, with a
direct handoff into the patient's clinical workspace.

## Backend Contract

### Endpoint

`GET /api/v1/dashboard/pending-investigations` (`backend/app/api/v1/endpoints/dashboard.py`)

| Parameter | Type | Default | Constraints |
|-----------|------|---------|-------------|
| `limit`   | int  | 100     | 1–500       |

Authenticated access only (`CurrentUserDependency`).

### Selection rules

- Candidate orders: `Investigation.is_current_year = true` **and**
  `lower(investigation_status)` in `("pending", "in_progress")` — exactly the
  orders the laboratory still owes results for under the Batch 66 workflow
  (released reports become `completed`; cancellations never surface).
- The annual-lifecycle guard keeps archived-year rows out of the feed.
- Ordered oldest-first by `requested_datetime` (then id) so ageing orders rise
  to the top of the backlog.
- Enrichment is batched (no N+1): one query for patients across all matched
  investigation rows.
- `age_hours` is derived from `requested_datetime` (naive-UTC normalised for
  SQLite) against the current UTC time, clamped non-negative.

### Response schemas

`PendingInvestigationItem` / `PendingInvestigationsResponse` in
`backend/app/schemas/dashboard.py`:

| Field | Notes |
|-------|-------|
| `investigation_id`, `investigation_number`, `investigation_name` | order identity |
| `investigation_status` | `pending` or `in_progress` |
| `patient_id`, `patient_name`, `patient_number` | batched patient enrichment |
| `case_type`, `visit_id`, `admission_id` | OPD/IPD encounter lineage |
| `requested_datetime`, `requested_by` | order origin |
| `age_hours` | hours since request, clamped ≥ 0 |
| `pending_count`, `in_progress_count` | headline workload aggregates |
| `as_of` | aware-UTC timestamp of the snapshot |

## Client Contract

- `getDashboardPendingInvestigations(options)` wrapper in `frontend/js/api.js`
  (`options.limit`, default 100).
- Dashboard "Pending investigations" panel in `frontend/js/dashboard.js`:
  - summary line `X pending · Y in progress`;
  - one card per order: investigation name as the title, then
    `patient (number) · investigation number · status · age hour(s) old`;
  - clicking a card navigates to the patients view and dispatches
    `hhms:open-patient-clinical` for direct handoff into the clinical
    workspace;
  - empty state ("No investigations are awaiting results.") and graceful
    unavailable-state on fetch failure, mirroring the sibling panels.

## Guarantees Locked by Tests

`backend/tests/test_dashboard_pending_investigations.py`:

1. Endpoint filters live open orders oldest-first with batched enrichment.
2. Schemas expose actionable identity, lineage and headline counts.
3. Frontend wrapper targets the correct route.
4. Dashboard panel renders with clinical-workspace handoff and graceful
   degradation.
5. Batch 66 result-workflow status transitions remain intact (regression lock).
6. Route is registered on the v1 API router.
