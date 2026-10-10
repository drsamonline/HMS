# Payment Method Collection Summary (Batch 96)

Per-method collection totals for the Reports & Printing workspace and the
dashboard feed. The printed packet runs through the **exact same** live
payment scan and per-method aggregation as the screen feed, so paper can
never drift from the dashboard for the same scan window.

## Endpoints

```
GET  /api/v1/dashboard/payment-method-summary?limit=200
POST /api/v1/reports/payment-method-summary-print-envelope
```

Both surfaces share one implementation
(`build_payment_method_summary_result` in
`backend/app/api/v1/endpoints/dashboard.py`):

- scans the most recent `limit` non-cancelled invoices (default 200,
  bounded 1–500 — same window as the Batch 89/90 ledger);
- sums every linked payment in a single grouped pass over the live
  `Payment` ledger joined to `Invoice` (no N+1; stored counters and
  status columns are never trusted).

## What it reports

Per payment method:

| Field | Meaning |
| --- | --- |
| `receipt_count` | receipts recorded under the method in the window |
| `invoice_count` | distinct invoices the method's payments were applied to |
| `gross_received` | raw sum of all receipt amounts |
| `collected` | amount actually absorbed by invoice balances (see invariant) |
| `share_of_total` | percentage (0–100) of the window's collected total |

Headlines: `as_of`, `invoices_checked`, `receipts_scanned`,
`methods_reported`, `total_collected`.

## Invariants

- **Batch 68 clamp parity:** receipts are charged to their invoice in
  chronological order (ties broken by receipt number); any amount beyond
  the invoice total counts as *gross received* but not as *collected*,
  and payments against invoices outside the scan window contribute
  nothing.
- `sum(per-method collected) == total_collected` always holds.
- Methods with no collected amount still appear (gross-only rows), sorted
  largest collector first with alphabetical tie-break for stability.
- Empty window → zero headlines and an empty ledger; the print preview
  renders a clean "No payments recorded in this scan window" fallback.

## Client integration points

- `frontend/js/api.js` — `getDashboardPaymentMethodSummary(options)` and
  `buildPaymentMethodSummaryPrintEnvelope(payload)`.
- `frontend/js/print.js` — `createPaymentMethodSummaryPrintPreview(host,
  {envelope})`: Collection Headlines + Per-Method Collection Ledger pages,
  envelope-first with a backward-compatible raw dashboard `{data}`
  fallback.
- `frontend/js/reports.js` — "Payment method collection summary" card
  (limit input + Prepare button) prepares through the print envelope.

## Print envelope schema

`PaymentMethodSummaryPrintEnvelope` (`report_type:
"payment_method_summary_print"`) wraps `title`, `generated_at` and
`PaymentMethodSummaryPrintData` with per-method
`PaymentMethodSummaryPrintLine` entries; all figures serialized as strings
for lossless printing.
