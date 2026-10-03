# Receivables Aging Ledger (Batch 86)

Financial-style aging of outstanding receivables, ready for on-screen review
and client-side printing. Built directly on the Batch 82 live-payment
outstanding-invoice derivation so the ledger always reconciles with the
dashboard receivables panel and the Batch 85 invoice print envelope.

## Backend

- `GET /api/v1/dashboard/receivables-aging?limit=200` (authenticated).
- Source: `billing_service.list_outstanding_invoices` — stale stored statuses
  and cancelled invoices never surface; balances are re-derived from live
  `Payment` rows each call.
- Reconciliation clamps (identical semantics to Batches 82/85):
  `amount_paid = min(sum(payments), total_amount)` and
  `balance_due = max(total_amount - amount_paid, 0)`, so printed figures
  always satisfy `total == paid + balance`.
- Standard buckets, emitted in stable order even when empty:
  `0-30 days`, `31-60 days`, `61-90 days`, `Over 90 days`
  (inclusive lower / exclusive upper bounds on invoice age in days).
- Per-item fields: invoice identity, patient name/number enrichment (batched,
  no N+1), totals, `days_outstanding`, and `bucket_label`.
- Headline aggregates: `invoice_count` and `total_outstanding`; bucket
  counts/totals sum back to these exactly.
- Schemas: `ReceivablesAgingBucket` / `ReceivablesAgingItem` /
  `ReceivablesAgingResponse` in `backend/app/schemas/dashboard.py`.

## Frontend

- API wrapper: `getDashboardReceivablesAging({limit})` in
  `frontend/js/api.js`.
- Print renderer: `createReceivablesAgingPrintPreview(host, {data, title})`
  in `frontend/js/print.js` — a bucket summary table (with grand-total row)
  plus a full aging ledger table on its own printed page.
- Reports & Printing workspace (`frontend/js/reports.js`): a "Receivables
  aging ledger" card with a limit input and *Prepare Aging Ledger* button
  that renders into the shared print-preview host.

## Tests

`backend/tests/test_receivables_aging_ledger.py` locks the endpoint wiring,
bucket stability, live-payment clamping, schema fields, frontend wrapper,
print renderer, workspace card, and this document's index entry.
