# Roadmap

High-level development milestones for HHMS — a LAN-based Homeopathic Hospital Management System.

**Status legend:** ✅ Complete · 🔄 In Progress · ⬜ Not Started

---

## Milestone 0 – Foundation ✅

- [x] Repository initialization
- [x] Project documentation
- [x] Development environment setup
- [x] Technology stack selection (Python server, HTML/CSS/JS client, WebView2 host, SQLite)
- [x] Architecture design
- [x] Master Specification frozen for v1.0

## Milestone 1 – Database ✅

- [x] Database schema design ([docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md))
- [x] Entity model frozen ([docs/DATABASE_ENTITIES.md](docs/DATABASE_ENTITIES.md))
- [x] Migration system setup (Alembic in `backend/`)
- [x] Data models implementation
- [ ] Seed data creation (final pass)

## Milestone 2 – Backend 🔄

- [x] API structure and routing ([docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md))
- [x] Authentication and authorization ([docs/SECURITY_ARCHITECTURE.md](docs/SECURITY_ARCHITECTURE.md))
- [x] Business logic implementation (functional batches through Batch 69)
- [x] Data access layer
- [x] Validation and error handling ([docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md))
- [ ] Performance/security audit
- [ ] Backup/restore and recovery hardening

## Milestone 3 – Frontend 🔄

- [x] UI framework setup (lightweight HTML/CSS/vanilla JS — see [docs/UI_GUIDELINES.md](docs/UI_GUIDELINES.md))
- [x] Page layouts and module shell
- [x] Form implementations (clinical, operational, administrative workspaces)
- [x] State management (client session/navigation)
- [ ] Cross-module client integration
- [ ] Role-aware UI

## Milestone 4 – Printing 🔄

- [x] Print manifest standard ([docs/PRINT_STANDARDS.md](docs/PRINT_STANDARDS.md))
- [x] Client print renderer and batch printing
- [ ] Prescription template final QA
- [ ] Printer hardware QA
- [ ] PDF generation verification

## Milestone 5 – Reports 🔄

- [x] Statistics engine and reporting foundation ([docs/STATISTICS_ENGINE.md](docs/STATISTICS_ENGINE.md))
- [x] Administrative and statistical report data (Batches 02–05)
- [ ] Report scheduling
- [ ] Final reporting/printing integration

## Milestone 6 – Testing ⬜

- [ ] Unit test suite expansion
- [ ] Integration tests across modules
- [ ] End-to-end tests
- [ ] Multi-client LAN tests
- [ ] Performance testing
- [ ] Clean-machine installation testing

## Milestone 7 – Release ⬜

- [ ] WebView2 runtime packaging
- [ ] Final EXE packaging (server + client)
- [ ] Documentation finalization
- [ ] Deployment scripts
- [ ] User training materials
- [ ] Production release

---

## Current Position

Functional application build is complete through **Batch 102 — Investigation Billing Reconciliation Feed & Print Envelope**;
the release effort has now entered **Batch 103 — Milestone 6 Comprehensive QA (in progress)**. Batch 103 delivers the shared
full-stack QA harness (`backend/tests/_qa_harness.py` — in-memory SQLite + real middleware/auth/service/DB layers) and the
end-to-end route suite `tests/test_batch103_qa_end_to_end.py` (10 tests: auth lifecycle incl. a login-500 product bug found
and fixed — `user.hashed_password` → `user.password_hash`; patient writes with sequence minting and text normalization;
handled-error paths for missing number sequences; all 14 dashboard feeds answering 200 on cold state). Full backend suite:
**391 passed**. Remaining Milestone 6 scope: cross-module integration tests, multi-client LAN testing, performance testing,
clean-machine installation testing — then Milestone 7 release packaging & deployment. Batch 102 itself (third mega-batch under
the amended D-008 policy: `GET /dashboard/investigation-billing-reconciliation` proves every open
lab order from the Batch 84 pending-investigation vocabulary still carries its billed amount on a live non-cancelled invoice —
billed amounts re-derived from `InvoiceItem` line totals in one grouped pass (`billed_amount == charged_total - credited_total`,
`pending_count + in_progress_count == total_investigations_checked`, `billed_count + billed_missing_count ==
total_investigations_checked`) via the shared `build_investigation_billing_reconciliation_scan`/`_result` trio, printable
through `POST /reports/investigation-billing-reconciliation-print-envelope` with screen/paper parity by construction; the
commit also restores the Batch 100 discharge-audit/OPD-queue print envelope service builders and locks the refund-audit
rollup to scan order (no silent re-sort) lost in an incomplete merge). **Batch 102 closes the remaining functional
surfaces: the next batch is Batch QA — Milestone 6 Comprehensive QA/debugging (unit/integration/E2E/LAN/performance/
clean-machine), followed by Milestone 7 release packaging & deployment.** Follows Batch 101's Ward Occupancy Print Envelope & Operational Print Completion
(second mega-batch under the amended D-008 policy: `GET /dashboard/ward-occupancy-summary` rolls active beds into
per-ward buckets — Unassigned bucketing, `occupied_beds + reserved_beds + available_beds == total_beds` for any input —
via the shared `build_ward_occupancy_summary_scan`/`build_ward_occupancy_summary_result` pair, printable through
`POST /reports/ward-occupancy-print-envelope`, with client renderers for the OPD queue summary and ward occupancy
envelopes completing the operational print track). Follows Batch 100's Settlement/Refund Audit Feeds & Operational
Print Envelopes (payment-analysis mega-batch: `GET /dashboard/invoice-settlement-audit` rolls the live reconciliation
scan into per-invoice settled/outstanding lines with refund counts (`settled_amount + outstanding_amount == total_amount`,
`cleared_count + unsettled_count == total_invoices`) via the shared `build_invoice_settlement_audit_result` /
`build_invoice_settlement_audit_scan` pair, while `GET /dashboard/refund-audit` flags every negative Payment row through
`invoice_exists` / `has_remarks` / `net_non_negative` → `processing_complete` (`processed_count + drifted_count ==
total_refunds`) via `build_refund_audit_result` / `build_refund_audit_scan`; four print envelopes — settlement audit,
refund audit, discharge audit and OPD queue summary — consume the Batch 99 "future print envelope" hooks by delegating to
the exact same dashboard scan/derivation functions, and the Batch 97 invoice overpayment ledger ghost card was wired into
the Reports & Printing workspace alongside cards for all new surfaces). Follows Batch 99's Discharge Audit & OPD Queue
Daily Summary (first mega-batch under D-008: `GET /dashboard/discharge-audit` reconciles every recent
discharge against admission status and bed occupancy through the shared `build_discharge_audit_result` /
`build_discharge_audit_scan` pair, while `GET /dashboard/opd-queue-summary` rolls live OPD token rows up per queue
day through `build_opd_queue_summary_result` / `build_opd_queue_summary_scan`, both surfaced as new dashboard panels
with API wrappers). Follows Batch 98's Payment Method Overpayment Breakdown
(`GET /dashboard/payment-method-overpayments` + `POST /reports/payment-method-overpayment-print-envelope` split
the scan window's over-collection across payment methods — per-method gross received, collected (Batch 68 clamp
parity) and overpaid remainder — through one shared derivation (`build_payment_method_overpayment_breakdown` /
`build_payment_method_overpayment_result`) behind both surfaces). Follows Batch 96's payment method collection
summary, Batch 95's collection summary print envelope
(`POST /reports/collection-summary-print-envelope` building the printable per-patient collection packet through the
exact shared scan/aggregation pair (`_build_reconciliation_rows` + `build_collection_summary_by_patient`) behind
`GET /dashboard/collection-summary-by-patient`), follows Batch 94's invoice payment reconciliation print envelope
(`POST /reports/invoice-payment-reconciliation-print-envelope` sharing `build_invoice_payment_reconciliation_ledger`
with the dashboard), follows Batch 93's receipt numbering continuity print envelope
(`POST /reports/receipt-numbering-continuity-print-envelope` sharing `build_receipt_numbering_continuity_result` with the dashboard),
follows Batch 92's invoice receipt continuity print envelope
(`POST /reports/invoice-receipt-continuity-print-envelope` sharing `_load_continuity_scan_inputs` /
`build_invoice_receipt_continuity_result` with the dashboard),
follows Batch 91's receivables aging print envelope
(`POST /reports/receivables-aging-print-envelope` sharing `build_receivables_aging_result` with the dashboard),
Batch 90's collection summary by patient (`GET
/dashboard/collection-summary-by-patient` + `POST /reports/collection-summary-print-envelope` rolling the
reconciliation ledger into per-patient totals via a shared scan/aggregation), Batch 89's invoice payment
reconciliation ledger (live per-invoice payment scan with derived-vs-stored status drift detection and a
printable reconciliation ledger; also fixed a reports.js attribute-quoting regression that had silently disabled
four ledger cards' Prepare buttons), Batch 88's whole-book receipt numbering continuity audit, Batch 87's
invoice-scoped receipt continuity report, Batch 86's receivables aging ledger, Batch 85's invoice print envelope,
Batch 84's laboratory pending-investigation feed, Batch 83's IPD bed-occupancy feed and Batch 82's
outstanding-billing feed). Remaining before QA: further cross-module workflow
continuity and server/client packaging & deployment (the final reporting/printing
integration track closed with Batch 100’s settlement/refund feeds, Batch 101’s ward occupancy feed + operational print envelopes and Batch 102’s investigation billing reconciliation feed + print envelope). Comprehensive QA/debugging begins after
cross-module integration, packaging, and final reporting/printing are complete.
**Batch-size policy (amended 2026-10-04, see D-008):** from Batch 99 onward the remaining surfaces are delivered
as mega-batches bundling 3–5 thematically-coherent features per commit (e.g. one payment-analysis batch, one
IPD/clinical-reporting batch) instead of one endpoint+envelope pair per batch, reducing total batch count while
keeping per-feature docs, tests and CHANGELOG sub-entries.
See [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md)
for the authoritative per-batch state and [CHANGELOG.md](CHANGELOG.md) for change history.
