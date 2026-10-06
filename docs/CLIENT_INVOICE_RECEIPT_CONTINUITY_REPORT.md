# Invoice Receipt Continuity Report (Batch 87)

Receipt-book integrity audit over live billing data, surfaced as a printable
continuity report in the Reports & Printing workspace. Extends the Batch 85
invoice print envelope and Batch 86 receivables aging ledger: where those
features report *what is owed*, this feed verifies *that every payment has a
properly numbered receipt*.

## Backend

- `GET /api/v1/dashboard/invoice-receipt-continuity?limit=200`
  (authenticated; limit bounded 1–500).
- Scope: the most recent non-cancelled invoices (`invoice_date DESC, id DESC`
  for deterministic ordering), enriched with patient name/number via one
  batched lookup (no N+1).
- Receipts are read from the live `Payment` ledger in a single grouped pass
  ordered by `payment_datetime, id`, so first/last receipt numbers per
  invoice are stable and stored counters are never trusted.
- Gap taxonomy (stable, printed verbatim):
  - `missing` — an invoice shows payments (live sum > 0) or a partial/paid
    status but has zero linked receipts. Uses the same Batch 82
    live-payment derivation semantics.
  - `duplicate` — the same receipt number appears more than once within an
    invoice's receipts.
  - `sequence_break` — the numeric suffixes of an invoice's receipts skip at
    least one value between first and last (span analysis via
    `_receipt_numeric_suffix`; only digit-terminated series are span-checked,
    everything else is treated as unstructured and skipped).
- Headline aggregates: `invoices_checked`, `invoices_with_receipts`,
  `invoices_missing_receipts`, `duplicate_receipt_count`,
  `sequence_break_count`. Every issue row carries `expected_count`,
  `actual_count`, `missing_count`, `first_receipt_number`,
  `last_receipt_number`, and `duplicate_receipt_numbers` so printed audits
  reconcile line-by-line.
- Schemas: `InvoiceReceiptGapItem` / `InvoiceReceiptContinuityResponse` in
  `backend/app/schemas/dashboard.py`.

## Frontend

- API wrapper: `getDashboardInvoiceReceiptContinuity({limit})` in
  `frontend/js/api.js`.
- Print renderer: `createInvoiceReceiptContinuityPrintPreview(host, {data,
  title})` in `frontend/js/print.js` — a continuity summary table (all five
  headline aggregates) plus a full issues table on its own printed page,
  with a "No continuity issues detected" clean-book fallback.
- Reports & Printing workspace (`frontend/js/reports.js`): an "Invoice
  receipt continuity report" card with limit input and *Prepare Continuity
  Report* button rendering into the shared print-preview host; the status
  line reports how many invoices were checked and how many issues were
  found.

## Tests

- `backend/tests/test_invoice_receipt_continuity_report.py` — 8 contract
  tests covering endpoint wiring and bounded limit, live-scan semantics
  (cancelled exclusion, deterministic order, single grouped receipt pass),
  gap taxonomy stability and span math, Batch 82 parity for missing-receipt
  detection, schema fields and exports, the frontend wrapper, the print
  renderer surfaces, and end-to-end workspace wiring.
- Full backend suite: 254 passed (246 → +8).
