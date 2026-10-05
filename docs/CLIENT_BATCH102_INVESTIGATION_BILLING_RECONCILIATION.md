# Batch 102 — Investigation Billing Reconciliation Feed & Print Envelope

> Status: **Completed** · Branch milestone: Batch 102 · Tests: 381 passing (see [../README.md](../README.md))

## Purpose

Closes the lab/billing boundary: every open laboratory order from the Batch 84
pending-investigation vocabulary must still carry its billed amount on a live,
non-cancelled invoice. This batch ships the dashboard proof feed and its
printable counterpart in one mega-batch (D-008 policy), plus restores two
Batch 100 contract items that were lost in an incomplete merge
(`build_discharge_audit_print_envelope`, `build_opd_queue_summary_print_envelope`
service builders and the refund-audit ordering fix).

## Dashboard feed — `GET /dashboard/investigation-billing-reconciliation`

Bounded limit (default 200, max 1000). Shared derivation trio (single source of
truth for screen + paper):

- `build_investigation_billing_reconciliation_scan(db, limit)` — one bounded scan
  of open investigations (`pending` / `in_progress`, case-insensitive) joined to
  Patient, plus one grouped pass over `InvoiceItem` lines on current-year,
  non-cancelled invoices. Billed amounts are re-derived from line totals — never
  trusted from any stored counter. Lines match investigations by
  `investigation_id` reference token in the description, falling back to the
  investigation-number prefix so legacy lines are covered. Negative line totals
  accumulate as credits instead of silently reducing charges.
- `build_investigation_billing_reconciliation_result(rows, as_of)` — pure rollup:
  - Every row satisfies `billed_amount == charged_total - credited_total`.
  - Headlines satisfy `pending_count + in_progress_count ==
    total_investigations_checked` and `billed_count + billed_missing_count ==
    total_investigations_checked`, with `total_billed == sum(billed_amount)`.
  - Unbilled open investigations surface with `billed_amount == 0` instead of
    disappearing — the same drift-surfacing philosophy as the Batch 89/97 ledgers.
  - `hours_since_request` is tz-safe and clamped non-negative (naive and
    aware `requested_datetime` values both handled).
- `build_investigation_billing_reconciliation(db, limit)` — entry point composing
  the pair against a single `as_of` snapshot; exported alongside the other two.

Schemas: `InvestigationBillingReconciliationItem` /
`InvestigationBillingReconciliationResponse` in
`backend/app/schemas/dashboard.py`, exported in `__all__`.

## Print envelope — `POST /reports/investigation-billing-reconciliation-print-envelope`

- Request: `InvestigationBillingReconciliationPrintRequest` (`limit` ge=1 /
  le=1000 default 200, optional `title` ≤200).
- Service builder `build_investigation_billing_reconciliation_print_envelope`
  delegates to the exact same scan/result pair as the dashboard feed, dropping
  only the dashboard-only keys (`visit_id`, `admission_id`) that fall outside the
  print-line contract — printed headlines always match the dashboard
  row-for-row (screen/paper parity by construction).
- Envelope discriminator: `report_type =
  "investigation_billing_reconciliation_print"`.
- Schemas: `InvestigationBillingReconciliationPrintRequest` /
  `InvestigationBillingReconciliationPrintLine` /
  `InvestigationBillingReconciliationPrintData` /
  `InvestigationBillingReconciliationPrintEnvelope` in
  `backend/app/schemas/reporting.py`, exported in `__all__`.

## Batch 100 restoration (carried by this commit)

The incomplete Batch 100 application had dropped two reporting-service builders;
both are restored and locked in by the existing Batch 100 suite (20/20 green):

- `ReportingService.build_discharge_audit_print_envelope` — reuses
  `build_discharge_audit_scan` / `build_discharge_audit_result` verbatim.
- `ReportingService.build_opd_queue_summary_print_envelope` — reuses
  `build_opd_queue_summary_scan` / `build_opd_queue_summary_result` verbatim.

Hardening alongside restoration: the refund-audit `net_non_negative` flag now
requires a present invoice net ledger (`net_paid is None` no longer passes), so
a refund whose parent-invoice re-sum is missing can never be reported
`processing_complete`. Row display order is the scan's newest-first ledger (the
rollup iterates in input order — no silent re-sort — so feed, screen and print
show exactly the same rows in exactly the same order).

## Client wiring

- `frontend/js/api.js`: `getDashboardInvestigationBillingReconciliation(options)`
  and `buildInvestigationBillingReconciliationPrintEnvelope(payload)`.
- `frontend/js/dashboard.js`: "Investigation billing reconciliation" panel —
  headline line (checked · pending · in progress · billed · unbilled · total
  billed) plus per-row cards flagging unbilled orders ("No live invoice line —
  bill it before reporting") with clinical-workspace hand-off like the Batch 83
  occupancy feed; degrades to its own empty/error state.
- `frontend/js/print.js`: `createInvestigationBillingReconciliationPrintPreview`
  (envelope-first with raw `{data}` fallback) — headline table + per-investigation
  charge/credit/net ledger.
- `frontend/js/reports.js`: "Investigation billing reconciliation" card (bounded
  Limit input + Prepare posting through the envelope; headline aggregates reported
  in the status box).

## Contract suite

`backend/tests/test_batch102_investigation_billing_reconciliation.py` (9 tests):
invoice-line reference-token matching (id token, number prefix, negative credit
lines, cancelled/other-type exclusion), rollup invariant round-trips, empty-scan
headline zeros, naive/tz-aware age clamping, schema exports, print-request bounds
and report-type discriminator, dashboard response shape, route registration for
both endpoints, and service reuse of the shared builders. Full suite: 381 passed.
