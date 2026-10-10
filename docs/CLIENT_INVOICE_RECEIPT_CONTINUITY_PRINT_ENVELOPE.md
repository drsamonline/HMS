# Invoice Receipt Continuity Print Envelope (Batch 92)

**Domain:** Reporting & Printing · Billing audit track
**Status:** Implemented and contract-tested

## Why this exists

Batch 87 shipped the invoice-to-receipt continuity **screen feed**
(`GET /dashboard/invoice-receipt-continuity`): it scans recent invoices and
flags `missing` receipts, `duplicate` receipt numbers and `sequence_break`
gaps in receipt numbering per invoice. Batch 91 did the same parity switch
for the receivables aging ledger; Batch 92 completes the pattern for the
continuity audit so finance staff can hand an auditor a printed packet that
provably matches what the dashboard shows.

Before this batch the Reports workspace card rendered the raw dashboard JSON
through the print preview. Screen and paper shared no enforced envelope, so
any future divergence in either surface would go unnoticed.

## One implementation, two surfaces

The audit derivation was extracted verbatim out of the endpoint into two
shared pieces inside `backend/app/api/v1/endpoints/dashboard.py`:

| Helper | Responsibility |
| --- | --- |
| `_load_continuity_scan_inputs(db, limit)` | Scans the most recent non-cancelled invoices (`invoice_date DESC, id DESC`, bounded `limit`) plus patients, and performs the **single grouped pass** over the `Payment` ledger collecting receipt numbers and live paid totals per invoice (no N+1; stored counters never trusted). |
| `build_invoice_receipt_continuity_result(...)` | Pure derivation of the audit: classifies each invoice's receipts into `missing` / `duplicate` / `sequence_break` issues and computes the headline aggregates (`invoices_checked`, `invoices_with_receipts`, `invoices_missing_receipts`, `duplicate_receipt_count`, `sequence_break_count`). |

Both the dashboard endpoint and the new print envelope call these helpers,
so **paper can never drift from screen** for the same scan window.

## Endpoints

| Surface | Route | Method |
| --- | --- | --- |
| Dashboard feed | `/api/v1/dashboard/invoice-receipt-continuity?limit=200` | GET |
| Print envelope | `/api/v1/reports/invoice-receipt-continuity-print-envelope` | POST |

Request body for the envelope: `{ "limit": 200, "title": "..." }` with
`limit` bounded `1..500` (same taxonomy as every billing report in this
track).

## Print schemas

Defined in `backend/app/schemas/reporting.py`:

* `InvoiceReceiptContinuityPrintRequest` — bounded `limit`, optional `title`.
* `InvoiceReceiptGapPrintLine` — one defect row; mirrors the dashboard
  `InvoiceReceiptGapItem` fields exactly (invoice/patient identity, `gap_type`,
  expected/actual/missing counts, first/last receipt number, duplicate list).
* `InvoiceReceiptContinuityPrintData` — headline aggregates **plus**
  `issue_count` (the envelope's convenience count of rows, replacing
  `len(issues)` on the client) and the `issues` lines.
* `InvoiceReceiptContinuityPrintEnvelope` — `report_type` literal
  `"invoice_receipt_continuity_print"`, `title`, `generated_at`, `data`.

Every aggregate sums back to `invoices_checked`, matching the Batch 87
reconciliation invariant.

## Frontend integration

* `frontend/js/api.js` — `buildInvoiceReceiptContinuityPrintEnvelope(payload)`.
* `frontend/js/print.js` — `createInvoiceReceiptContinuityPrintPreview` is now
  **envelope-first** (`{envelope=null,data=null}` with
  `const src=envelope?.data??data??{}`), keeping backward compatibility with
  raw dashboard payloads. Renders the *Continuity Summary* table and the
  *Continuity Issues* page (clean empty-state fallback when no defects).
* `frontend/js/reports.js` — the "Invoice receipt continuity report" card now
  prepares through the print envelope instead of the dashboard feed; the
  status line reads envelope headline aggregates
  (`${d.invoices_checked} invoice(s) checked, ${d.issue_count} issue(s)`).
  The unused `getDashboardInvoiceReceiptContinuity` import was dropped.

## Contract tests

`backend/tests/test_invoice_receipt_continuity_print_envelope.py` locks the
shared-helper extraction, endpoint/service reuse, schema shape and exports,
the api wrapper, the envelope-aware renderer, the Reports workspace parity
switch, and this document's presence in `docs/INDEX.md`. The Batch 87 test
file's workspace-wiring assertions were updated to the envelope convention.

## See also

* [CLIENT_INVOICE_RECEIPT_CONTINUITY_REPORT.md](CLIENT_INVOICE_RECEIPT_CONTINUITY_REPORT.md) — the Batch 87 screen feed
* [CLIENT_RECEIVABLES_AGING_PRINT_ENVELOPE.md](CLIENT_RECEIVABLES_AGING_PRINT_ENVELOPE.md) — the Batch 91 parity precedent
* [CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md](CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md) — global receipt-number series gaps (Batch 88)
