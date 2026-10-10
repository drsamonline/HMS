# Collection Summary by Patient (Batch 90)

Rolls the Batch 89 invoice payment reconciliation ledger up into per-patient
collection totals so front-desk and finance staff can print a single
"who owes what, who has paid" summary across the most recent billing window.

## Why this exists

The reconciliation ledger answers *per invoice*; management reviews ask the
question *per patient*. Batch 90 reuses the exact same live-payment scan —
one grouped pass over the `Payment` ledger, stored counters never trusted,
amounts clamped to the invoice total — and aggregates it by patient, so the
printed packet can never drift from the on-screen ledger line-for-line.

## Endpoints

### `GET /api/v1/dashboard/collection-summary-by-patient`

| Parameter | Default | Bounds | Meaning |
| --- | --- | --- | --- |
| `limit` | `200` | 1–500 | Number of non-cancelled invoices scanned (invoice_date DESC, id DESC). |

Response (`PatientCollectionSummaryResponse`):

- Headlines: `as_of`, `invoices_checked`, `patients_checked`,
  `patients_with_outstanding`, `total_billed`, `total_collected`,
  `total_outstanding`.
- `items` (`PatientCollectionSummaryItem`, first-appearance order preserved):
  `patient_id`, `patient_name`, `patient_number`, `invoice_count`,
  `paid_invoice_count`, `partial_invoice_count`, `unpaid_invoice_count`,
  `total_billed`, `total_collected`, `outstanding`, `last_payment_date`.

Invariants (asserted by contract tests):

- `invoices_checked == sum(item.invoice_count)` and
  `patients_checked == len(items)`.
- Per patient and in headline totals:
  `total_collected + outstanding == total_billed` (each row's clamped
  amounts contribute exactly once).
- Derived-status taxonomy matches Batch 89: `paid` ⇔ fully collected,
  `unpaid` ⇔ nothing collected, otherwise `partial`.

### `POST /api/v1/reports/collection-summary-print-envelope`

Body (`CollectionSummaryPrintRequest`): `limit` (same bounds), optional
`title`. Returns `CollectionSummaryPrintEnvelope` with stringified money
fields and ISO `last_payment_date`, built by the shared
`build_collection_summary_by_patient` aggregation in the dashboard module.

## Frontend integration

- `frontend/js/api.js` — `getDashboardCollectionSummaryByPatient(options)`
  and `buildCollectionSummaryPrintEnvelope(payload)`.
- `frontend/js/print.js` — `createCollectionSummaryPrintPreview(host, {data,title})`
  renders a **Collection Summary Headlines** section and a **Per-Patient
  Collection Ledger** table (with an empty-state fallback).
- `frontend/js/reports.js` — "Collection summary by patient" card in the
  Reports & Printing workspace (Limit input + Prepare button + status line).

## Shared-code guarantee

Both surfaces call `_build_reconciliation_rows(db, limit)` followed by
`build_collection_summary_by_patient(rows)`; there is no second payment scan
and no duplicate aggregation implementation, so print and screen agree by
construction.
