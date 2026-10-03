# Collection Summary Print Envelope (Batch 95)

Printable per-patient collection summary packet for the Reports & Printing
workspace. The envelope runs through the **exact same** live-payment scan and
aggregation as the dashboard feed, so printed headlines can never drift from
the screen for the same scan window.

## Endpoint

```
POST /api/v1/reports/collection-summary-print-envelope
```

Request body (`CollectionSummaryPrintRequest`):

| Field   | Type        | Constraints                     |
| ------- | ----------- | ------------------------------- |
| `limit` | `int`       | default `200`, bounds `1–500`   |
| `title` | `str\|None` | max 200 chars                   |

Response: `CollectionSummaryPrintEnvelope` with `report_type`
`"collection_summary_print"`, a `title`, `generated_at`, and `data`
(`CollectionSummaryPrintData`).

## Shared derivation semantics

The service function `build_collection_summary_print_envelope`
(`backend/app/services/reporting.py`) delegates to the Batch 90 shared
helpers in `backend/app/api/v1/endpoints/dashboard.py`:

- `_build_reconciliation_rows(db, limit)` — scans the most recent non-cancelled
  invoices (`invoice_date DESC, id DESC`) and sums payments in a **single
  grouped pass** over the Payment ledger (no N+1). Stored counters/status are
  never trusted; `amount_paid` is clamped to `total_amount` and
  `balance_due` is non-negative (Batch 68 invariant
  `amount_paid + balance_due == total_amount`).
- `build_collection_summary_by_patient(rows)` — rolls the reconciliation rows
  up per patient into billed / collected / outstanding totals with derived
  paid/partial/unpaid invoice counts and the latest payment timestamp.

Because both `GET /dashboard/collection-summary-by-patient` and this print
envelope call the same two functions, one implementation serves both surfaces.

## Invariants on every printed packet

- `total_billed == total_collected + total_outstanding`
- per-patient: `total_billed == total_collected + outstanding`
- headline counts sum back exactly:
  `invoices_checked == Σ invoice_count` and
  `patients_checked == len(items)`
- `patients_with_outstanding <= patients_checked`

## Client integration points

- `frontend/js/api.js` — `buildCollectionSummaryPrintEnvelope(payload)` posts
  to the endpoint above.
- `frontend/js/print.js` — `createCollectionSummaryPrintPreview(host, {envelope})`
  renders the Headlines section and the Per-Patient Collection Ledger page;
  accepts raw dashboard `{data}` as a backward-compatible fallback and returns
  `{envelope, data}`.
- `frontend/js/reports.js` — the "Collection summary by patient" card
  (`#collection-summary-limit` / `#collection-summary-prepare`) prepares
  through the print envelope instead of the raw dashboard feed.

## Related documents

- [CLIENT_COLLECTION_SUMMARY_BY_PATIENT.md](CLIENT_COLLECTION_SUMMARY_BY_PATIENT.md) — dashboard feed (Batch 90)
- [CLIENT_INVOICE_PAYMENT_RECONCILIATION_LEDGER.md](CLIENT_INVOICE_PAYMENT_RECONCILIATION_LEDGER.md) — underlying ledger (Batch 89)
