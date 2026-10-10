# Payment Method Overpayment Breakdown (Batch 98)

**Domain:** Reporting & Printing · Billing audit track
**Status:** Implemented and contract-tested

## Why this exists

Batch 97 shipped the invoice overpayment ledger
(`GET /dashboard/invoice-overpayments`): it flags *which invoices* were paid
beyond their billed amount using the unclamped live Payment totals. Batch 96
shipped the per-method collection summary
(`GET /dashboard/payment-method-summary`), whose clamp hides excess
receipts inside `gross_received` only as an aggregate gap. Batch 98 closes
the loop and answers *which payment methods* produced the excess: a
per-method breakdown of gross received vs collected vs overpaid, printable
through the same envelope-first pattern used by Batches 91-96.

## One implementation, two surfaces

The derivation lives once in `backend/app/api/v1/endpoints/dashboard.py`:

| Helper | Responsibility |
| --- | --- |
| `build_payment_method_overpayment_breakdown(receipts, invoice_totals, invoices_checked)` | Pure rollup reusing the Batch 96 `build_payment_method_collection_summary` verbatim for the collected side, then charging receipts chronologically (ties by receipt number) against invoice totals so every amount beyond the balance is attributed to its method as `overpaid`. Invariants: per-row `gross_received == collected + overpaid`, headline `total_gross == total_collected + total_overpaid`, and `sum(per-method overpaid) == total_overpaid`. |
| `build_payment_method_overpayment_result(db, limit)` | Scan entry point shared with the reporting service: most recent `limit` non-cancelled invoices (`invoice_date DESC, id DESC`) plus one pass over the linked Payment ledger joined to Invoice (no N+1; stored counters and status columns never trusted). |

Both `GET /dashboard/payment-method-overpayments` and
`POST /reports/payment-method-overpayment-print-envelope` call these
helpers, so **paper can never drift from screen** for the same scan window.

## Endpoints

| Surface | Route | Method |
| --- | --- | --- |
| Dashboard feed | `/api/v1/dashboard/payment-method-overpayments?limit=200` | GET |
| Print envelope | `/api/v1/reports/payment-method-overpayment-print-envelope` | POST |

Request body for the envelope: `{ "limit": 200, "title": "..." }` with
`limit` bounded `1..500` — the same taxonomy as every billing report in
this track.

## Schemas

Dashboard (`backend/app/schemas/dashboard.py`):
`PaymentMethodOverpaymentItem` (payment_method, receipt_count,
invoice_count, gross_received, collected, share_of_total, overpaid) and
`PaymentMethodOverpaymentResponse` (as_of, invoices_checked,
receipts_scanned, methods_reported, methods_with_overpayment, total_gross,
total_collected, total_overpaid, items). Both exported in `__all__`.

Reporting (`backend/app/schemas/reporting.py`):
`PaymentMethodOverpaymentPrintRequest`, `PaymentMethodOverpaymentPrintLine`
(stringified decimals per the print-schema convention),
`PaymentMethodOverpaymentPrintData` and
`PaymentMethodOverpaymentPrintEnvelope` with `report_type` literal
`"payment_method_overpayment_print"`. All exported.

## Service & endpoint wiring

* `ReportingService.build_payment_method_overpayment_print_envelope`
  (`backend/app/services/reporting.py`) delegates to
  `build_payment_method_overpayment_result` — no copy of the aggregation.
* `POST /reports/payment-method-overpayment-print-envelope`
  (`backend/app/api/v1/endpoints/reporting.py`) wired with
  `response_model=PaymentMethodOverpaymentPrintEnvelope`.

## Frontend integration

* `frontend/js/api.js` — `getDashboardPaymentMethodOverpayments(options)`
  and `buildPaymentMethodOverpaymentPrintEnvelope(payload)`.
* `frontend/js/print.js` — `createPaymentMethodOverpaymentPrintPreview`
  is envelope-first (`{envelope=null,data=null}` with
  `const payload=envelope?.data??data??{}`), rendering an *Overpayment
  Breakdown Summary* table (invoices checked, receipts scanned, methods
  reported/with overpayment, gross/collected/overpaid headlines) and a
  *Per-Method Overpayment Ledger* page (Method, Receipts, Invoices, Gross
  Received, Collected, Share %, Overpaid) with a clean empty-state
  fallback.
* `frontend/js/reports.js` — new "Payment method overpayment breakdown"
  card (limit input + Prepare button, single-escaped id convention)
  prepares through the print envelope; the status line reads envelope
  headline aggregates
  (`${d.methods_with_overpayment} of ${d.methods_reported} method(s) carry
  excess, overpaid ${d.total_overpaid} of gross ${d.total_gross}`).

## Contract tests

`backend/tests/test_payment_method_payment_method_overpayment_breakdown.py`
locks the shared-helper extraction, dashboard delegation, service/endpoint
reuse, schema fields/exports, API wrappers, the envelope-aware renderer,
the Reports workspace card wiring and this document's presence in
`docs/INDEX.md`.

## See also

* [CLIENT_INVOICE_OVERPAYMENT_LEDGER.md](CLIENT_INVOICE_OVERPAYMENT_LEDGER.md) — the Batch 97 invoice-level ledger
* [CLIENT_PAYMENT_METHOD_COLLECTION_SUMMARY.md](CLIENT_PAYMENT_METHOD_COLLECTION_SUMMARY.md) — the Batch 96 collection summary (clamp parity source)
* [CLIENT_COLLECTION_SUMMARY_PRINT_ENVELOPE.md](CLIENT_COLLECTION_SUMMARY_PRINT_ENVELOPE.md) — the Batch 95 parity precedent
