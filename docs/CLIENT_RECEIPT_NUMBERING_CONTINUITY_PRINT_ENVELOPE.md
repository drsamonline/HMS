# Receipt Numbering Continuity Print Envelope (Batch 93)

## Purpose

Give billing staff a **printable whole-receipt-book numbering audit** that is
guaranteed to match the on-screen audit from Batch 88 line-for-line. This
completes screen/paper parity for the receipt-numbering track, following the
same envelope pattern as the aging ledger (Batch 91) and the invoice receipt
continuity report (Batch 92).

## Endpoint

```
POST /api/v1/reports/receipt-numbering-continuity-print-envelope
```

Request body (`ReceiptNumberingContinuityPrintRequest`):

| Field   | Type | Default | Bounds          |
|---------|------|---------|-----------------|
| `limit` | int  | 2000    | 1 … 5000        |
| `title` | str? | null    | max 200 chars   |

Response: `ReceiptNumberingContinuityPrintEnvelope` with
`report_type: "receipt_numbering_continuity_print"`, `title`, `generated_at`
and a `data` page (`ReceiptNumberingContinuityPrintData`) carrying
`as_of`, `receipts_checked`, `series_count`, `clean_series_count`,
`total_gap_count` and per-series rows (`ReceiptSeriesPrintLine`:
`prefix`, `first_number`, `last_number`, `expected_count`, `actual_count`,
`gap_count`, `missing_numbers`, `duplicate_numbers`).

## Shared derivation (one implementation, two surfaces)

The Batch 88 dashboard scan was extracted into
`build_receipt_numbering_continuity_result(db, limit)` in
`backend/app/api/v1/endpoints/dashboard.py`. Both surfaces call it:

* `GET /dashboard/receipt-numbering-continuity` wraps its dict in
  `ReceiptNumberingContinuityResponse`;
* `reporting_service.build_receipt_numbering_continuity_print_envelope`
  maps it into the print envelope.

Semantics inherited unchanged:

* single ordered pass over the live `Payment` ledger
  (`payment_datetime ASC, id ASC`, receipts with non-null numbers only) —
  no N+1, stored counters never trusted;
* series = every receipt sharing the same non-digit prefix, parsed with the
  shared `_receipt_numeric_suffix` helper so this audit stays consistent with
  the per-invoice Batch 87 continuity report;
* per-series reconciliation invariant always holds:
  `expected_count == actual_count + gap_count`
  (`expected_count` spans first…last numeric value inclusive);
* `missing_numbers` detail is capped at 200 entries per series, but
  `gap_count` always reflects the true number of missing values;
* non-numeric receipt numbers are counted in `receipts_checked` but never
  produce false gaps;
* aggregates satisfy `clean_series_count <= series_count` and
  `total_gap_count == sum(gap_count)`.

## Frontend integration

* `frontend/js/api.js` — `buildReceiptNumberingContinuityPrintEnvelope(payload)`.
* `frontend/js/print.js` — `createReceiptNumberingContinuityPrintPreview`
  now accepts `{envelope}` with backward-compatible `{data}` fallback;
  renders Audit Summary, Receipt Series Summary, Missing Numbers Detail and
  Duplicate Receipt Numbers pages.
* `frontend/js/reports.js` — the "Receipt numbering continuity" card's
  Prepare button posts through the print envelope (no longer the raw
  dashboard feed) and reports headline aggregates in the status line.

## Invariants (locked by contract tests)

1. Dashboard endpoint and print envelope share
   `build_receipt_numbering_continuity_result` — no second implementation.
2. Per-series `expected_count == actual_count + gap_count` on printed rows.
3. `clean_series_count <= series_count`; `total_gap_count` equals the sum of
   series `gap_count`s.
4. Printed figures reconcile with the dashboard feed for the same scan window.

See `backend/tests/test_receipt_numbering_continuity_print_envelope.py`.
