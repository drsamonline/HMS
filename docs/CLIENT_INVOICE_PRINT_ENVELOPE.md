# Invoice Print Envelope (Batch 85)

Client-side printable invoice packet assembled by the reporting service and rendered
in the Reports & Printing workspace. Follows reporting/print batches 02–05 and closes
the loop between the Batch 68 billing-consistency invariants and printed output.

## Endpoint

`POST /api/v1/reports/invoice-print-envelope` (authenticated)

Request body (`InvoicePrintRequest`, `backend/app/schemas/reporting.py`):

- `invoice_id` — target invoice.

Response (`InvoicePrintEnvelope`):

- Header identity: invoice number/date, patient name/number, case/visit lineage where available.
- Line items: description, quantity, unit price, line amount.
- Totals with live payment-derived balances:
  - `total_amount` — invoice total.
  - `amount_paid` — sum of recorded payments, clamped to `total_amount`.
  - `balance_due` — non-negative; reconciliation invariant `amount_paid + balance_due == total_amount` holds for every envelope (mirrors Batch 68).

## Service

`ReportingService.build_invoice_print_envelope` (`backend/app/services/reporting.py`)
reads balances from live payment rows rather than stored status fields, so a stale
`payment_status` can never misprint an invoice as paid/outstanding.

## Client wiring

- `buildInvoicePrintEnvelope(invoiceId)` wrapper in `frontend/js/api.js`.
- `createInvoicePrintPreview(envelope)` structured HTML renderer in `frontend/js/print.js`
  (invoice details, line-item table, totals and receipt summary), routed through the
  standard print renderer pipeline.
- UI controls in the Reports & Printing workspace (`frontend/js/reports.js`) select an
  invoice and display the preview before printing.

## Tests

`backend/tests/test_invoice_print_envelope.py` (5 tests): service logic incl. balance
clamping/reconciliation, endpoint registration, schema validation and frontend
integration points. Full suite: 238 passed.
