# Invoice Payment Reconciliation Ledger (Batch 89)

Whole-book invoice-to-payment reconciliation, surfaced as a printable ledger
in the Reports & Printing workspace. Where Batch 82's outstanding feed and
Batch 86's aging ledger only show invoices with a balance, this feed
reconciles **every** scanned invoice against the live `Payment` ledger so
billing staff can prove collection state line-by-line — paid, partially paid
and unpaid alike — and spot drift between the stored status column and what
the payments actually say.

## Backend

- `GET /api/v1/dashboard/invoice-payment-reconciliation?limit=200`
  (authenticated; limit bounded 1–500).
- Scope: the most recent `limit` non-cancelled invoices (`invoice_date DESC,
  id DESC`), the same deterministic scan window as the Batch 87 continuity
  report.
- Payments are summed in a single grouped pass over the `Payment` table for
  all scanned invoices (no N+1); stored counters and status columns are never
  trusted.
- Per-invoice reconciliation (Batch 68 atomic-consistency parity):
  - `amount_paid` = live payment total clamped to `total_amount`;
  - `balance_due` = non-negative remainder;
  - invariant on every row: `amount_paid + balance_due == total_amount`;
  - `derived_payment_status` (unpaid / partial / paid) computed from those
    live figures via `_derive_payment_status`, reported next to the stored
    `payment_status`; `is_reconciled` flags drift between the two;
  - `receipt_count` = number of receipt rows recorded against the invoice in
    the same pass.
- Headline aggregates: `invoices_checked`, `paid_invoices`,
  `partially_paid_invoices`, `unpaid_invoices` (always summing back to
  `invoices_checked`) plus `total_billed`, `total_paid` and
  `total_outstanding` satisfying `total_billed == total_paid +
  total_outstanding` so printed ledgers reconcile.
- Schemas: `InvoicePaymentReconciliationItem` /
  `InvoicePaymentReconciliationResponse` in
  `backend/app/schemas/dashboard.py`.

## Frontend

- API wrapper: `getDashboardInvoicePaymentReconciliation({limit})` in
  `frontend/js/api.js`.
- Print renderer: `createInvoicePaymentReconciliationPrintPreview(host, {data,
  title})` in `frontend/js/print.js` — a reconciliation summary table (all
  seven headline aggregates), the full per-invoice reconciliation ledger page
  (invoice, patient, totals, stored vs derived status, receipts, reconciled
  mark) and a Status Drift Detail page listing only rows whose derived status
  disagrees with the stored one, with a "No status drift detected." clean
  fallback.
- Reports & Printing workspace (`frontend/js/reports.js`): an "Invoice payment
  reconciliation ledger" card with limit input and *Prepare Reconciliation
  Ledger* button rendering into the shared print-preview host; the status
  line reports how many invoices were checked, the total paid and the total
  outstanding.

## Tests

- `backend/tests/test_invoice_payment_reconciliation_ledger.py` — 6 contract
  tests covering endpoint wiring and bounded limit, live-payment scan
  semantics (single grouped pass, cancelled exclusion, Batch 68 clamping
  parity), derived-status taxonomy, schema fields and exports, the frontend
  wrapper/renderer/workspace integration points, and documentation indexing.
- Full backend suite: 266 passed (260 → +6).
