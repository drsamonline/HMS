# Batch 78 — Clinical Cross-Module Workflow Continuity

## Purpose

Homoeopathic practice is inherently longitudinal: a case spans multiple
encounters, each follow-up references the prescription that guided it and the
prescription planned next. Before this batch, those links were unvalidated
foreign keys and there was no way to ask the system "what is due today?" or
"show every prescription for this case". Batch 78 closes both gaps without
creating duplicate models, services or frontend modules.

## Surfaces

### 1. Follow-up prescription lineage validation (`app/services/followup.py`)

`_validate_prescription(db, prescription_id, patient_id)` runs on `create()`
and `update()` for both `previous_prescription_id` and `next_prescription_id`:

* unknown id → `ResourceNotFoundException("Prescription not found.")`
* prescription whose visit belongs to another patient → `ValidationException`

This prevents cross-patient linkage of clinical decisions (a referential
integrity gap: SQLite foreign keys alone do not enforce patient scoping).

Archived prescriptions (post-rollover) may legitimately have a NULL
`visit_id`; such rows pass the ownership check because their identity is
already fixed by the archive-reference layer (Batch 77).

### 2. Due-follow-up window (`list_due`, `GET /followups`)

`FollowUpService.list_due(db, from_datetime, to_datetime, skip, limit)` returns
follow-ups whose `next_followup_datetime` falls inside the window, ordered
ascending. Exposed as:

```
GET /api/v1/followups?due_from=<iso>&due_to=<iso>[&skip=&limit=]
```

`due_from`/`due_to` must be supplied together; omitting both preserves the
existing `case_record_id` query contract used by the clinical workspace.

Client wrapper: `listDueFollowups(fromIso, toIso, options)` in
`frontend/js/api.js`.

### 3. Case-wide prescriptions (`get_by_case`, `GET /prescriptions/by-case/{id}`)

A case record's clinical history spans its primary visit plus any later visits
linked back via `Visit.case_record_id`. The new read collects all three layers:

* repository `PrescriptionRepository.get_by_visits(db, visit_ids)` — batch read
* service `PrescriptionService.get_by_case(db, case_record_id)` — visit-set
  resolution + case existence check
* endpoint `GET /api/v1/prescriptions/by-case/{case_record_id}` — registered
  **before** the generic `/{prescription_id}` route so path matching is correct

Client wrapper: `listCasePrescriptions(caseRecordId)`.

## Testing

`backend/tests/test_clinical_workflow_continuity.py` — five static contract
tests locking the service/API/client surfaces (consistent with the project's
contract-test style). Full backend suite: **210 passed**.

Environment note: the container had drifted to pytest 9.x / pytest-asyncio
1.4, which aborts collection ("Marks cannot be applied to fixtures"). The
pinned ranges in `backend/pyproject.toml` (`pytest>=8.3,<9`,
`pytest-asyncio>=0.25,<1`) are authoritative; reinstall within them after any
image refresh.

## Next

Wire the due-window into the clinician dashboard (today/this-week widgets) and
the case-workspace prescription timeline during subsequent continuity batches,
then proceed to packaging/deployment and reporting/printing integration.
