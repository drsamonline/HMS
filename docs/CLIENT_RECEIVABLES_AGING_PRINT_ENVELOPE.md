# Receivables Aging Print Envelope (Batch 91)

Client-facing specification for turning the Batch 86 receivables aging
ledger into a first-class printable packet, prepared through the reporting
print-envelope surface instead of the dashboard feed.

## Why

The Batch 86 dashboard feed (`GET /api/v1/dashboard/receivables-aging`)
already derives standard 0-30 / 31-60 / 61-90 / Over-90 buckets from live
payments. But printing went straight off the dashboard payload, so the
Reports & Printing workspace had no envelope-backed packet for aging —
unlike invoices (Batch 5x), receipt continuity (Batch 87), numbering
audits (Batch 88), reconciliation (Batch 89) and collection summaries
(Batch 90). Batch 91 closes that gap with **one shared derivation**:
screen and paper can never drift because both call the same function.

## Contract

- `POST /api/v1/reports/receivables-aging-print-envelope` accepts
  `{ "limit": 1..500 (default 200), "title": optional (<=200 chars) }`
  and returns a `ReceivablesAgingPrintEnvelope`:
  - `report_type: "receivables_aging_print"`, `title`, `generated_at`
  - `data.as_of`, `data.buckets[]`, `data.items[]`,
    `data.invoice_count`, `data.total_outstanding`
- The service reuses the Batch 82 live-payment outstanding scan
  (`billing_service.list_outstanding_invoices`, single grouped Payment
  pass — stored counters are never trusted) and the shared
  `build_receivables_aging_result` bucketing extracted from the dashboard
  endpoint in this batch.
- Invariants (identical to the dashboard feed):
  - every row satisfies `amount_paid + balance_due == total_amount`
    with `amount_paid` clamped to the invoice total (Batch 68 parity);
  - fully settled invoices never appear; cancelled invoices are excluded;
  - all four buckets are always present, even when empty, so printed
    ledgers keep a stable shape;
  - bucket counts sum to `invoice_count` and bucket totals sum to
    `total_outstanding`.

## Frontend

- `frontend/js/api.js`: `buildReceivablesAgingPrintEnvelope(payload)`.
- `frontend/js/print.js`: `createReceivablesAgingPrintPreview(host,
  {envelope})` renders the packet (header with as-of date, Aging Buckets
  summary table with total row, page-broken Aging Ledger detail table).
  It still accepts a raw dashboard payload via `{data}` for backward
  compatibility; envelope data takes precedence and the envelope's own
  `title` wins over the caller default.
- `frontend/js/reports.js`: the "Receivables aging ledger" card now
  prepares the packet through the print envelope endpoint (previously it
  consumed the dashboard feed directly). The status line reports the
  envelope headline aggregates.

## Guarantees

- Printed aging always reconciles line-for-line with
  `GET /dashboard/receivables-aging` (same code path, same day).
- No N+1: payments aggregate in one grouped query; patients batch-load.
- Empty state prints "Nothing outstanding — the ledger is clear".
