# Client Dashboard — Laboratory Pending-Investigation Continuity

**Status:** Active (Batch 84) · **Module:** Dashboard / Laboratory · **Audience:** clinicians, laboratory staff, administrators

## Purpose

Batch 66 (Laboratory Result Workflow Completion) made investigation status a trustworthy
monotonic signal: orders start `pending`, move to `in_progress` when results are verified
and to `completed` when released; cancelled orders never receive results. Batch 84 turns
that state into an actionable dashboard feed so the outstanding laboratory workload is
visible without opening the investigations module — which orders are still awaiting
results, for which patients, how long they have been waiting, and a direct handoff into
the patient's clinical workspace.

## Backend Contract

### Endpoint

`GET /api/v1/dashboard/pending-investigations` (`backend/app/api/v1/endpoints/dashboard.py`)

| Parameter | Type | Default | Constraints |
|-----------|------|---------|-------------|
| `limit`   | int  | 100     | 1–200       |

Authenticated access only (`CurrentUserDependency`).

### Selection & prioritisation rules

- Candidate orders: `lower(investigation_status)` in `("pending", "in_progress")` —
  exactly the two non-terminal states of the Batch 66 workflow. Completed and cancelled
  orders never surface.
- Ordering is oldest-first (`requested_datetime ASC`, then `id ASC`), so the longest
  waiting order heads the list.
- Enrichment is batched (no N+1): one query for patients across all order patient ids.
- `age_hours` is derived from `requested_datetime` (naive-UTC normalised for SQLite)
  against the current UTC time, clamped non-negative.
- Headline aggregates: `pending_count` and `in_progress_count` over the returned page.

### Response schema

`PendingInvestigationsResponse` (`backend/app/schemas/dashboard.py`):

- `as_of` — aware UTC timestamp of evaluation
- `items[]` (`PendingInvestigationItem`) — `investigation_id`, `investigation_number`,
  `patient_id`, `patient_name`, `patient_number`, `investigation_name`,
  `investigation_status`, `requested_datetime`, `requested_by`, `visit_id`,
  `admission_id`, `age_hours`
- `pending_count` — rows in `pending` state on this page
- `in_progress_count` — rows in `in_progress` state on this page

## Client Wiring

- API wrapper `getDashboardPendingInvestigations(options)` in `frontend/js/api.js`.
- Dashboard panel **"Pending investigations"** in `frontend/js/dashboard.js`:
  - summary line with pending / in-progress counts;
  - one card per order showing investigation name, patient identity, order number,
    status and age in hours;
  - cards navigate to the patients view and dispatch `hhms:open-patient-clinical`,
    the same handoff used by the due-follow-up (Batch 79) and bed-occupancy
    (Batch 83) panels;
  - graceful unavailable-state on fetch failure.

## Tests

Contract suite `backend/tests/test_dashboard_pending_investigations.py` locks the
endpoint selection/ordering rules, schema fields, client wrapper, dashboard panel and
the Batch 66 workflow reliance.
