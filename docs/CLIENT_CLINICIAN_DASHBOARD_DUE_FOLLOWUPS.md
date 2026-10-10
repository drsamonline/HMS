# Clinician Dashboard — Due Follow-up Continuity (Batch 79)

Turns the Batch 78 due-window service query (`FollowUpService.list_due`) into an
actionable clinician workflow feed on the client dashboard.

## Backend contract

`GET /api/v1/dashboard/due-followups` (authenticated, any role with dashboard access)

| Parameter | Default | Constraints | Notes |
|---|---|---|---|
| `from_datetime` | now (UTC) | ISO datetime | Pass an earlier value to surface overdue follow-ups. |
| `days_ahead` | 7 | 0–365 | Window length from the start bound. |
| `limit` | 100 | 1–200 | Page size; ordered ascending by scheduled datetime. |

Response (`DueFollowUpsResponse`):

```json
{
  "from_datetime": "2026-09-29T00:00:00",
  "to_datetime": "2026-10-06T00:00:00",
  "items": [
    {
      "followup_id": 12,
      "case_record_id": 3,
      "patient_id": 7,
      "patient_name": "Asha Rao",
      "patient_number": "OPD-2026-0007",
      "case_number": "CASE-2026-0003",
      "next_followup_datetime": "2026-10-02T09:30:00",
      "previous_prescription_id": 41,
      "decision": "wait"
    }
  ]
}
```

Implementation notes:
- SQLite stores naive UTC datetimes; aware inputs are normalised via
  `_naive_utc()` before comparison so window filters behave consistently.
- Patient and case identity are enriched with two batched `IN` lookups
  (no N+1 per follow-up row).
- Files: `backend/app/api/v1/endpoints/dashboard.py`,
  `backend/app/schemas/dashboard.py`; router registered in
  `backend/app/api/v1/api.py`.

## Client wiring

- `frontend/js/api.js`: `getDashboardDueFollowups({ from, daysAhead, limit })`.
- `frontend/js/dashboard.js`: "Due follow-ups (next 7 days)" panel renders
  patient cards; clicking a card dispatches `hhms:open-patient-clinical`
  (`detail.patientId`) so the shell opens the clinical workspace directly on
  that patient — dashboard → clinical handoff without search.
- Fetch failures degrade to an "unavailable right now" empty state; the
  dashboard never blocks on this feed.

## Data capture loop

The due list is only as good as its data: the follow-up form in
`frontend/js/clinical.js` now captures `next_followup_datetime`
(datetime-local input) and saved follow-up cards display the scheduled next
visit. Batch 78's prescription-lineage validation applies to the same records.

## Tests

`backend/tests/test_clinician_dashboard_due_followups.py` (7 tests) locks:
endpoint module + schema existence, due-window service usage and enrichment
fields, router registration (source import/include and live route table),
frontend wrapper/rendering/event contracts, and follow-up form field capture.
