# Receipt Numbering Continuity Audit (Batch 88)

Whole-receipt-book numbering integrity audit, surfaced as a printable audit in
the Reports & Printing workspace. Extends the Batch 87 invoice receipt
continuity report: where Batch 87 checked receipts *per invoice*, this feed
checks every receipt number against its own numeric **series**, so billing
staff can see missing numbers and duplicates across the entire receipt book
rather than one invoice at a time.

## Backend

- `GET /api/v1/dashboard/receipt-numbering-continuity?limit=2000`
  (authenticated; limit bounded 1–5000).
- Scope: the most recent `limit` live `Payment` ledger rows carrying a
  receipt number, read in a single ordered pass (`payment_datetime ASC, id
  ASC`) — no N+1 queries, stored counters are never trusted.
- Series grouping: every receipt sharing the same non-digit prefix (e.g. `R`
  in `R000123`) forms one series. Numeric suffixes are parsed with the Batch
  87 `_receipt_numeric_suffix` helper so both audits agree on what "numeric"
  means; non-numeric receipt numbers are counted in `receipts_checked` but
  never produce false gaps.
- Per-series findings:
  - `missing_numbers` — values skipped between the first and last issued
    number (sequence gaps in the physical receipt book); the detail list is
    capped at 200 entries per series, while `gap_count` always reflects the
    true number of missing values.
  - `duplicate_numbers` — receipt numbers recorded more than once.
  - per-series reconciliation that always holds:
    `expected_count == actual_count + gap_count`, where `expected_count`
    spans first..last inclusive.
- Headline aggregates: `receipts_checked`, `series_count`,
  `clean_series_count` (series with neither gaps nor duplicates) and
  `total_gap_count`, which sums back to the scanned ledger so printed audits
  reconcile.
- Schemas: `ReceiptSeriesGap` / `ReceiptNumberingContinuityResponse` in
  `backend/app/schemas/dashboard.py`.

## Frontend

- API wrapper: `getDashboardReceiptNumberingContinuity({limit})` in
  `frontend/js/api.js`.
- Print renderer: `createReceiptNumberingContinuityPrintPreview(host, {data,
  title})` in `frontend/js/print.js` — an audit summary table (all four
  headline aggregates), a per-series summary table, a Missing Numbers Detail
  page (one block per gapped series with a "No numbering gaps detected."
  clean-book fallback) and a Duplicate Receipt Numbers table.
- Reports & Printing workspace (`frontend/js/reports.js`): a "Receipt
  numbering continuity" card with limit input and *Prepare Numbering Audit*
  button rendering into the shared print-preview host; the status line
  reports how many receipts were checked, how many series were found and the
  total missing-number count.

## Tests

- `backend/tests/test_receipt_numbering_continuity.py` — 6 contract tests
  covering endpoint wiring and single-pass ledger scan, Batch 87 parser
  reuse, per-series reconciliation fields, schema fields and exports, the
  frontend wrapper, the print renderer surfaces, end-to-end workspace wiring,
  and documentation indexing.
- Full backend suite: 260 passed (254 → +6).
