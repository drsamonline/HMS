# Invoice Overpayment Ledger (Batch 97)

## Purpose

The Batch 89/94 invoice payment reconciliation ledger deliberately **clamps**
`amount_paid` to `total_amount` (Batch 68 semantics), which hides
over-collection: an invoice paid beyond its billed total still shows as fully
paid with a zero balance. The **Invoice Overpayment Ledger** surfaces exactly
what that clamp conceals — every invoice in the scan window whose live,
un-clamped payment total exceeds its billed amount, together with the
overpaid remainder.

## Dashboard feed

- Endpoint: `GET /dashboard/invoice-overpayments`
- Bounded scan: `limit` query parameter, default **200**, min **1**, max **500**
  (same window as the Batch 89/90/94/96/98 ledgers).
- Response schema: `InvoiceOverpaymentResponse` (`backend/app/schemas/dashboard.py`)
  with per-row `InvoiceOverpaymentItem` entries.

### Derivation

Single shared implementation behind both surfaces:

- `build_overpayment_ledger(db, limit)` — scan entry point exported by
  `backend/app/api/v1/endpoints/dashboard.py`. It reuses the exact
  `_build_reconciliation_rows` grouped Payment pass from the reconciliation
  ledger (one query over the Payment table joined to non-cancelled invoices;
  stored counters and status columns are never trusted). The un-clamped paid
  total (`total_paid_raw`) rides on every reconciliation row, so no second
  re-sum is needed.
- `build_overpayment_ledger_result(rows, as_of)` — pure rollup used by the
  scan and directly testable: keeps only rows where
  `total_paid_raw > total_amount`, computes `overpaid_amount =
  total_paid_raw - total_amount`, and produces headline aggregates.

### Invariants

Every response satisfies, by construction:

```text
overpaid_amount == total_paid_raw - total_amount      # per row
invoices_checked == invoices_overpaid == len(items)   # only overpaid rows kept
total_paid_raw == total_billed + total_overpaid       # headlines
```

## Print envelope

- Endpoint: `POST /reports/invoice-overpayment-print-envelope`
- Service builder: `build_invoice_overpayment_print_envelope` in
  `backend/app/services/reporting.py` delegates to the same
  `build_overpayment_ledger` scan — screen and paper can never drift.
- Schemas in `backend/app/schemas/reporting.py`:
  `InvoiceOverpaymentPrintRequest` (bounded limit, optional title ≤ 200),
  `InvoiceOverpaymentPrintLine` (monetary values as strings),
  `InvoiceOverpaymentPrintData`, `InvoiceOverpaymentPrintEnvelope`
  (`report_type: "invoice_overpayment_print"`).

## Client wiring

- `frontend/js/api.js`: `getDashboardInvoiceOverpayments(options)` and
  `buildInvoiceOverpaymentPrintEnvelope(payload)`.
- `frontend/js/print.js`: `createInvoiceOverpaymentPrintPreview()` —
  envelope-first with a raw-dashboard `{data}` fallback.
- `frontend/js/reports.js`: **"Invoice overpayment ledger" card** in the
  Reports & Printing workspace (limit input + Prepare button posting through
  the envelope). Note: this card was missing when Batch 97 shipped (the
  server surface was complete but unreachable from the UI); it was wired in
  **Batch 100** as the ghost-card fix.

## Testing

Contract coverage lives in
`backend/tests/test_batch100_settlement_refund_audit_print_envelopes.py`,
which includes dedicated round-trips for `build_overpayment_ledger_result`
(invariant checks, empty-scan handling) closing the documented-but-untested
gap left by Batch 97.
