# Invoice Payment Reconciliation Print Envelope (Batch 94)

Client-facing specification for the printable invoice payment reconciliation
packet. The envelope shares the exact live-payment scan and aggregation behind
the dashboard feed, so **screen and paper can never drift**.

## Endpoint

```
POST /api/v1/reports/invoice-payment-reconciliation-print-envelope
```

Request body (`InvoicePaymentReconciliationPrintRequest`):

| Field   | Type   | Constraints                        |
|---------|--------|------------------------------------|
| `limit` | int    | default 200, bounded 1–500         |
| `title` | str?   | optional, max length 200           |

Response (`InvoicePaymentReconciliationPrintEnvelope`,
`report_type: "invoice_payment_reconciliation_print"`): headline aggregates
plus one `InvoicePaymentReconciliationPrintLine` per scanned invoice, mirroring
`InvoicePaymentReconciliationItem` from the dashboard feed field-for-field
(monetary values serialized as strings).

## Shared derivation

Both surfaces call the single implementation
`build_invoice_payment_reconciliation_ledger(db, limit)` in
`backend/app/api/v1/endpoints/dashboard.py`, which in turn uses
`_build_reconciliation_rows(db, limit)`:

- Scans the most recent `limit` non-cancelled invoices
  (`invoice_date DESC, id DESC`).
- Sums payments in **one grouped pass** over the Payment ledger — no N+1
  queries; stored counters and stored status are never trusted.
- Per invoice: `amount_paid` clamped to `total_amount`, non-negative
  `balance_due`, invariant `amount_paid + balance_due == total_amount`
  (Batch 68 parity).
- Derived payment status (`unpaid` / `partial` / `paid`) via
  `_derive_payment_status`; stored-vs-derived drift flagged with
  `is_reconciled`.

## Invariants (print envelope)

For any scan window:

1. `paid_invoices + partially_paid_invoices + unpaid_invoices == invoices_checked`
2. `total_billed == total_paid + total_outstanding`
3. Every printed line reconciles exactly with the corresponding row of
   `GET /dashboard/invoice-payment-reconciliation` (same limit ⇒ same rows).

## Client integration

- `frontend/js/api.js`: `buildInvoicePaymentReconciliationPrintEnvelope(payload)`
  posts the request and returns the envelope.
- `frontend/js/print.js`: `createInvoicePaymentReconciliationPrintPreview(host,
  {envelope})` renders Summary, full Reconciliation Ledger and Status Drift
  Detail pages; accepts a raw dashboard `{data}` payload as fallback for
  backward compatibility (envelope data/title take precedence).
- `frontend/js/reports.js`: the "Invoice payment reconciliation ledger" card in
  the Reports & Printing workspace prepares through the print envelope
  (limit input + Prepare button); the status line reports envelope aggregates.

## Related documents

- [CLIENT_INVOICE_PAYMENT_RECONCILIATION_LEDGER.md](CLIENT_INVOICE_PAYMENT_RECONCILIATION_LEDGER.md) — Batch 89 dashboard feed specification.
