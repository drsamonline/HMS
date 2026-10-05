# Settlement/Refund Audit Feeds & Operational Print Envelopes (Batch 100)

**Domain:** Dashboard payment-analysis track · Reports & Printing integration
**Status:** Implemented and contract-tested
**Mega-batch note:** delivered under the amended mega-batching policy
(D-008) — two new dashboard feeds, four print envelopes, one ghost-card fix
and the Batch 97/98 test-gap closure in a single commit.

## Why this exists

The Batch 96–98 collection track answered *how much was collected* and
*where excess landed*. Two questions remained unanswered:

1. **How far has each invoice been collected?** The Batch 89 reconciliation
   ledger flags derived-vs-stored status drift and the Batch 97 ledger
   flags over-collection, but neither shows the settled/outstanding split
   per invoice with cleared headlines.
2. **Were refunds processed cleanly?** Negative `Payment` rows are
   refunds/adjustments; the billing rules require each to reference a live
   invoice, carry an explanatory remarks note and leave net collections
   non-negative — yet no surface audited those guarantees.

Batch 99 exported its discharge-audit and OPD-queue derivations "for a
future print envelope". That hook is now consumed: both operational feeds
gain printable packets that reuse the exact same scans line-for-line.

Finally, the Batch 97 **Invoice Overpayment Ledger** was server-complete
(`GET /dashboard/invoice-overpayments`,
`POST /reports/invoice-overpayment-print-envelope`, schemas, API wrapper,
renderer) but had **no card in the Reports & Printing workspace** — an
unreachable surface. This batch wires it in (ghost-card fix).

## One implementation, every surface (screen/paper parity by construction)

All five envelopes delegate to the shared scan/derivation helpers in
`backend/app/api/v1/endpoints/dashboard.py`:

| Helper | Responsibility |
| --- | --- |
| `build_invoice_settlement_audit_result(rows, as_of)` | Pure rollup over clamped reconciliation rows: `settled_amount + outstanding_amount == total_amount` per row (Batch 68 clamp reused verbatim), `is_cleared` ⇔ zero outstanding, headlines satisfy `cleared_count + unsettled_count == total_invoices` and `total_billed == total_collected + total_outstanding`. Over-collection stays visible via `overpayment_amount` without breaking the clamp. |
| `build_invoice_settlement_audit_scan(db, limit)` | Reuses `_build_reconciliation_rows` (the Batch 89/90/94/97 grouped Payment pass — no N+1, stored counters never trusted) plus one grouped refund-count pass (`Payment.amount_paid < 0`). |
| `build_refund_audit_result(rows, as_of)` | Pure per-refund flagging: `invoice_exists`, `has_remarks` (non-empty after strip), `net_non_negative`, `processing_complete` = all three. Newest-first; `processed_count + drifted_count == total_refunds`. Orphaned refunds surface instead of disappearing. |
| `build_refund_audit_scan(db, limit)` | Capped newest-first scan of negative `Payment` rows joined to Invoice, with one grouped pass re-summing each referenced invoice's un-clamped net ledger. |
| `build_discharge_audit_scan/_result` (Batch 99) | Reused verbatim by the new discharge audit envelope. |
| `build_opd_queue_summary_scan/_result` (Batch 99) | Reused verbatim by the new queue summary envelope. |

## Endpoints

| Surface | Route | Method | Bounds |
| --- | --- | --- | --- |
| Settlement audit feed | `/api/v1/dashboard/invoice-settlement-audit` | GET | `limit` default 200, `1..500` |
| Refund audit feed | `/api/v1/dashboard/refund-audit` | GET | `limit` default 200, `1..500` |
| Settlement audit envelope | `/api/v1/reports/invoice-settlement-audit-print-envelope` | POST | `limit` `1..500`, optional `title ≤ 200` |
| Refund audit envelope | `/api/v1/reports/refund-audit-print-envelope` | POST | `limit` `1..500`, optional `title ≤ 200` |
| Discharge audit envelope | `/api/v1/reports/discharge-audit-print-envelope` | POST | `limit` `1..500`, optional `title ≤ 200` |
| OPD queue summary envelope | `/api/v1/reports/opd-queue-summary-print-envelope` | POST | `limit_days` default 14, `1..90` |

All require authentication (`CurrentUserDependency`).

## Schemas

Dashboard (`backend/app/schemas/dashboard.py`): `InvoiceSettlementAuditItem`,
`InvoiceSettlementAuditResponse`, `RefundAuditItem`, `RefundAuditResponse`.

Reporting (`backend/app/schemas/reporting.py`) — Request/Line/Data/Envelope
per surface, stringified-decimal print lines per the print-schema
convention, `report_type` discriminators:
`invoice_settlement_audit_print`, `refund_audit_print`,
`discharge_audit_print`, `opd_queue_summary_print`.

## Frontend

* `frontend/js/api.js` — `getDashboardInvoiceSettlementAudit`,
  `getDashboardRefundAudit`, `buildInvoiceSettlementAuditPrintEnvelope`,
  `buildRefundAuditPrintEnvelope`, `buildDischargeAuditPrintEnvelope`,
  `buildOPDQueueSummaryPrintEnvelope` (plus the previously orphaned
  `buildInvoiceOverpaymentPrintEnvelope` now actually used).
* `frontend/js/print.js` — envelope-aware preview renderers
  `createInvoiceSettlementAuditPrintPreview`,
  `createRefundAuditPrintPreview`, `createDischargeAuditPrintPreview`,
  `createOPDQueueSummaryPrintPreview`.
* `frontend/js/reports.js` — five new/connected cards in the Reports &
  Printing workspace: Invoice overpayment ledger (ghost-card fix), Invoice
  settlement audit, Refund processing audit, Discharge audit ledger, OPD
  queue daily summary — each with a bounded limit input, a Prepare button
  posting through the matching print envelope, and headline aggregates
  reported in the workspace status box.

## Contract tests

`backend/tests/test_batch100_settlement_refund_audit_print_envelopes.py`
locks in: pure-derivation invariant round-trips for the settlement and
refund scans (including empty-scan and whitespace-remarks edge cases), the
Batch 97 `build_overpayment_ledger_result` and Batch 98
`build_payment_method_overpayment_breakdown` derivations (closing the
documented-but-untested gap), endpoint/service wiring (shared-scan reuse,
bounded query params, response models), route registration on the app,
schema exports/validation, frontend wrappers/renderers/cards, the
ghost-card fix itself, and this document's INDEX entry.
