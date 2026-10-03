# HHMS Project State

## Authoritative baseline
- Baseline: current repository state on `master` (commit 8123205), reconstructed from the latest user-supplied full ZIP (`HMS(5).zip`) plus every committed batch since. The ZIP is no longer used as a reconstruction source; this repo tree is authoritative going forward (rule 9 checkpoint satisfied at Batch 85).
- Latest completed functional milestone: Batch 93 — Receipt Numbering Continuity Print Envelope.
- Current milestone: Batch 90 (annual lifecycle complete for case, visit, billing, pharmacy, prescription lineage, IPD, laboratory, MRD, procurement and inventory domains; follow-up/prescription continuity surfaces landed; due-follow-up workflow feed wired into the client dashboard; outstanding-billing receivables feed wired into the client dashboard; IPD bed-occupancy continuity feed wired into the client dashboard; laboratory pending-investigation backlog feed wired into the client dashboard; invoice print envelope landed as the first reporting/printing integration step beyond the clinical print batches; receivables aging ledger landed with bucketed endpoint, API wrapper, printable aging preview in the Reports & Printing workspace, contract tests and documentation; invoice receipt continuity report landed with missing/duplicate/sequence-break audit over live payments, API wrapper, printable continuity audit in the Reports & Printing workspace, 8 contract tests and documentation; receipt numbering continuity audit landed with whole-book series gap/duplicate reconciliation, API wrapper, printable numbering audit in the Reports & Printing workspace, 6 contract tests and documentation; invoice payment reconciliation ledger landed with live per-invoice payment scan, derived-vs-stored status drift detection, API wrapper, printable reconciliation ledger in the Reports & Printing workspace, 7 contract tests, a reports.js attribute-quoting regression fix restoring the four ledger cards' Prepare buttons and documentation).; collection summary by patient landed with per-patient rollup of the reconciliation ledger via a shared scan/aggregation, printable collection summary envelope, API wrappers, preview renderer, Reports workspace card, 8 contract tests and documentation).; receivables aging print envelope landed with the Batch 86 bucketing extracted into the shared `build_receivables_aging_result` derivation, printable aging envelope endpoint + schemas, API wrapper, envelope-aware aging preview renderer, Reports workspace card switched to the envelope, 7 contract tests and documentation).; invoice receipt continuity print envelope landed with the Batch 87 audit extracted into the shared `_load_continuity_scan_inputs` scan + `build_invoice_receipt_continuity_result` derivation, printable continuity envelope endpoint + schemas (headline aggregates plus `issue_count`), API wrapper, envelope-aware continuity preview renderer with dashboard fallback, Reports workspace card switched to the envelope, 7 contract tests and documentation).; receipt numbering continuity print envelope landed with the Batch 88 whole-book audit extracted into the shared `build_receipt_numbering_continuity_result` derivation, printable numbering envelope endpoint + schemas (`ReceiptNumberingContinuityPrintRequest`/`ReceiptSeriesPrintLine`/`PrintData`/`PrintEnvelope`), API wrapper, envelope-aware numbering preview renderer with dashboard fallback, Reports workspace numbering card switched to the envelope and documentation (contract test suite pending as part of this batch closeout).
- Current project phase: Functional application build and cross-module integration.
- Comprehensive QA/debugging has NOT started as the primary phase.

## Locked workflow
1. Build functional application code first.
2. Combine logically related work into the largest safe batch whenever technically coherent.
3. Audit the actual generated ZIP against the intended change set before issuing any `git add` command.
4. Use one combined verification/staging command sequence per batch.
5. Keep commit/push separate until GREEN.
6. Fix defects that block the current feature immediately; defer broad hardening to QA.
7. Do not create duplicate models, services, endpoints, or frontend modules.
8. Clean only confirmed generated/stale/duplicate clutter.
9. Use fresh full-project baselines at major checkpoints or when the current tree cannot be reconstructed safely.

## Data lifecycle — LOCKED
- Patient master remains live regardless of encounter age.
- Current operational year remains live.
- Years 2–5 are online, read-only annual archives loaded on demand.
- Years 6–10 are cold archives accessed only when explicitly requested.
- A renewed case in a new operational year becomes a new live CaseRecord in the same case family and links to the prior case.
- Operational year may be calendar year or configurable financial year.
- Actual clinical timestamps remain authoritative.
- Generic cleanup never deletes clinical/business data.
- Safe maintenance may clean generated runtime artifacts, checkpoint WAL, run SQLite optimization and create verified backups.
- VACUUM is administrator-triggered.

## Batch 55 functional addition
- Patient Timeline can load live patient activity normally.
- Archived case history can be explicitly loaded by selecting a verified historical year.
- Historical records remain read-only through this access path.
- The client does not attach all archive databases during normal operation.
- Existing archive and operational-year APIs remain the source of truth.

## Batch 69 — Annual Case Rollover
- Added verified pre-rollover backup before annual case archival.
- Added permanent `CaseArchiveReference` records so patient/case identity survives physical live-database removal.
- Added administrator-only rollover preview and execution endpoints plus System Health UI action.
- Rollover physically removes `Diagnosis`, `FollowUp` and `CaseRecord` rows for the selected completed operational year after archive preparation.
- Live `renewed_from_case_id` references are cleared when they would point at a physically archived case; `case_family_id` remains the longitudinal linkage.
- The verified annual archive remains a read-only-by-convention SQLite snapshot and is checksum/integrity validated.
- Other encounter, billing, pharmacy and administrative rows remain live until their own lifecycle metadata and rollover rules are implemented.

## Batch 70 — Encounter Annual Lifecycle & Rollover
- `Visit` now carries lifecycle metadata (`visit_year`, `storage_tier`, `is_current_year`) derived from the encounter date via the operational-year configuration at creation time (migration `0021_visit_operational_year_lifecycle` backfills existing rows).
- Permanent `VisitArchiveReference` records preserve visit identity and archive linkage after physical live-database removal.
- Annual rollover physically removes completed-year `Visit` rows alongside cases: `CaseRecord.visit_id` links are detached first, references are created before deletion, and post-rollover validation confirms no live rows for the rolled-over year remain.
- Archived visits are readable on demand through `/maintenance/archives/{year}/patients/{patient_id}/visits` (client wrapper `getHistoricalArchiveVisits`); historical reads come from the verified annual archive snapshot.
- Rollover preview reports `visit_count` for the target year.

## Batch 71 — Billing Annual Lifecycle & Rollover
- `Invoice` and `Payment` now carry lifecycle metadata (`invoice_year`/`payment_year`, `storage_tier`, `is_current_year`) derived from the billing date via the operational-year configuration at creation time (migration `0022_billing_operational_year_lifecycle` backfills existing rows; `Payment.invoice_id` made nullable).
- Permanent `InvoiceArchiveReference` and `PaymentArchiveReference` records preserve billing identity and archive linkage after physical live-database removal.
- Annual rollover physically removes completed-year invoices and payments alongside cases and visits: child payments are detached from archived invoices first, references are created before deletion, and post-rollover validation confirms no live billing rows for the rolled-over year remain.
- Archived billing is readable on demand through `/maintenance/archives/{year}/patients/{patient_id}/invoices|payments` (client wrappers `getHistoricalArchiveInvoices` / `getHistoricalArchivePayments`); historical reads come from the verified annual archive snapshot.
- Rollover preview reports `invoice_count` and `payment_count` for the target year; `InvoiceRead`/`PaymentRead` schemas expose the lifecycle fields.

## Batch 72 — Pharmacy Annual Lifecycle & Rollover
- `DispenseRecord` now carries lifecycle metadata (`dispense_year`, `storage_tier`, `is_current_year`) derived from the dispense date via the operational-year configuration at creation time (migration `0023_pharmacy_operational_year_lifecycle` backfills existing rows; `prescription_item_id` made nullable).
- Permanent `DispenseArchiveReference` records preserve dispense identity and archive linkage after physical live-database removal.
- Annual rollover physically removes completed-year dispense records alongside cases, visits and billing: references are created before deletion, and post-rollover validation confirms no live pharmacy rows for the rolled-over year remain.
- Archived dispensing is readable on demand through `/maintenance/archives/{year}/patients/{patient_id}/dispenses` (client wrapper `getHistoricalArchiveDispenses`), joined through the PrescriptionItem→Prescription→Visit lineage inside the verified annual archive snapshot.
- Rollover preview reports `dispense_count` for the target year; `DispenseRead` schema exposes the lifecycle fields.

## Batch 73 — IPD Annual Lifecycle & Rollover
- `Admission` carries lifecycle metadata (`admission_year`, `storage_tier`, `is_current_year`) derived from the admission datetime via operational-year configuration at creation (migration `0024_ipd_operational_year_lifecycle` backfills existing rows).
- Permanent `AdmissionArchiveReference` records preserve admission identity and lineage after physical live-database removal.
- Annual rollover physically archives completed-year admissions: preview reports `admission_count`, references are created before deletion, investigations requested during archived admissions are detached safely, and post-rollover validation confirms no live IPD rows remain for the year.
- Archived IPD episodes are readable through `/maintenance/archives/{year}/patients/{patient_id}/admissions` (client wrapper `getHistoricalArchiveAdmissions`); `AdmissionRead` exposes the lifecycle fields.

## Batch 74 — Laboratory Annual Lifecycle & Rollover
- `Investigation` and `InvestigationResult` carry lifecycle metadata (`investigation_year`/`result_year`, `storage_tier`, `is_current_year`) derived at creation via operational-year configuration (migration `0025_lab_operational_year_lifecycle` backfills existing rows).
- Permanent `InvestigationArchiveReference` records preserve investigation identity and visit/admission lineage after physical live-database removal.
- Annual rollover physically archives completed-year investigations together with their results; preview reports `investigation_count` and post-rollover validation confirms no live laboratory rows remain for the year.
- Archived laboratory orders are readable through `/maintenance/archives/{year}/patients/{patient_id}/investigations` (client wrapper `getHistoricalArchiveInvestigations`); read schemas expose the lifecycle fields.

## Batch 75 — MRD Annual Lifecycle & Rollover
- `MedicalDocument` carries lifecycle metadata (`document_year`, `storage_tier`, `is_current_year`) derived at creation via operational-year configuration (migration `0026_mrd_operational_year_lifecycle` backfills existing rows).
- Permanent `MedicalDocumentArchiveReference` records preserve document identity and visit/admission lineage after physical live-database removal.
- Annual rollover physically archives completed-year medical documents; preview reports `document_count`, post-rollover validation confirms no live MRD rows remain for the year, and results include `documents_archived`.
- Archived MRD documents are readable through `/maintenance/archives/{year}/patients/{patient_id}/documents` (client wrapper `getHistoricalArchiveDocuments`); `MedicalDocumentRead` exposes the lifecycle fields.

## Batch 76 — Procurement & Inventory Annual Lifecycle & Rollover
- `PurchaseOrder`, `GoodsReceipt`, `StockTransaction` and `StockCard` carry lifecycle metadata (`order_year`/`receipt_year`/`transaction_year`, `storage_tier`, `is_current_year`) derived at creation via operational-year configuration (migration `0027_procurement_inventory_operational_year_lifecycle` backfills existing rows).
- Permanent `PurchaseOrderArchiveReference`, `GoodsReceiptArchiveReference`, `StockTransactionArchiveReference` and `StockCardArchiveReference` records preserve procurement/inventory identity after physical live-database removal.
- Annual rollover physically archives completed-year purchase orders, goods receipts, stock transactions and stock-card ledger entries; preview reports `purchase_order_count`, `goods_receipt_count`, `stock_transaction_count` and `stock_card_count`, and post-rollover validation confirms no live rows remain for the year.
- Master data (Supplier, Medicine, InventoryItem) and live StockBatch balance rows are never rolled over: batches carry current `quantity_remaining` that dispensing depends on; only document/ledger rows participate in annual archival.
- Archived procurement/inventory rows are readable through administrator-only, year-scoped endpoints `/maintenance/archives/{year}/purchase-orders|goods-receipts|stock-transactions|stock-cards` (no patient lineage exists on these records, so the patient-scoped pattern does not apply); client wrappers `getHistoricalPurchaseOrders`, `getHistoricalGoodsReceipts`, `getHistoricalStockTransactions`, `getHistoricalStockCards`.
- Read schemas expose lifecycle fields; contract test suite `backend/tests/test_procurement_archive_rollover.py` (full suite 195 passed).
- Fixed a startup-blocking FastAPI defect: 204-status DELETE routes (`/maintenance/backups/{name}`, `/billing/invoice-items/{item_id}`) now declare `response_model=None` explicitly.

## Remaining before QA
- Complete remaining cross-module workflow continuity.
- Complete server/client packaging and deployment workflow.
- Complete final reporting/printing integration.
- Then comprehensive QA/debugging, performance/security testing, recovery testing, clean-machine testing and release validation.

## Batch 83 — IPD Bed-Occupancy Continuity
- New endpoint `GET /dashboard/bed-occupancy` (`backend/app/api/v1/endpoints/dashboard.py`) reconciles every active bed marked occupied/reserved against its live admission (status pair `admitted`/`active`, mirroring the Batch 61 concurrency guard), ward-ordered, with batched admission/patient enrichment (no N+1) and per-row `length_of_stay_days` (naive-UTC normalised for SQLite, clamped non-negative).
- Drift visibility: beds whose occupancy flag has no matching active admission are still returned with `has_active_admission=false` and null admission fields so data issues surface instead of silently disappearing.
- Schemas `BedOccupancyItem`/`BedOccupancyResponse` in `backend/app/schemas/dashboard.py` expose bed identity (number/ward/room/type), admission lineage (id/number/datetime/status), patient name/number and headline `occupied_count`/`total_beds` aggregates with aware-UTC `as_of`.
- Client wiring: `getDashboardBedOccupancy(options)` wrapper in `frontend/js/api.js`; dashboard "IPD bed occupancy" panel with occupied-of-total summary; reconciled cards navigate to the patients view and dispatch `hhms:open-patient-clinical`; drift rows render a check-IPD-records notice and are disabled; graceful unavailable-state on fetch failure.
- Documentation: `docs/CLIENT_DASHBOARD_BED_OCCUPANCY.md` added and indexed in `docs/INDEX.md`.
- Contract suite `backend/tests/test_dashboard_bed_occupancy.py` (5 tests incl. Batch 61 guarantee regression locks; full suite 227 passed).

## Batch 84 — Laboratory Pending-Investigation Dashboard Feed
- New endpoint `GET /dashboard/pending-investigations` (`backend/app/api/v1/endpoints/dashboard.py`) surfacing the live laboratory backlog: `Investigation` rows with `is_current_year=true` and status `pending`/`in_progress` (the exact open-order pair of the Batch 66 result workflow), oldest-first by `requested_datetime`.
- Per-row enrichment: patient name/number via batched lookup (no N+1), investigation number/name/status, encounter lineage, requester and naive-UTC-normalised `age_hours` clamped non-negative; `pending_count`/`in_progress_count` aggregates and aware-UTC `as_of` exposed by `PendingInvestigationItem`/`PendingInvestigationsResponse` in `backend/app/schemas/dashboard.py`.
- Client wiring: `getDashboardPendingInvestigations(options)` wrapper in `frontend/js/api.js`; dashboard "Pending investigations" panel whose cards dispatch `hhms:open-patient-clinical` for clinical-workspace handoff; empty/unavailable states mirror sibling panels.
- Documentation: `docs/CLIENT_DASHBOARD_PENDING_INVESTIGATIONS.md` added and indexed in `docs/INDEX.md`.
- Contract suite `backend/tests/test_dashboard_pending_investigations.py` (6 tests incl. Batch 66 regression lock); full suite 233 passed.

## Batch 85 — Invoice Print Envelope for Reporting Integration
- Service `ReportingService.build_invoice_print_envelope` (`backend/app/services/reporting.py`) assembles a printable invoice packet: header identity, line items, totals with live payment-derived balances (`amount_paid` clamped to total, non-negative `balance_due`, reconciliation `paid + balance == total`).
- New endpoint `POST /reports/invoice-print-envelope` (`backend/app/api/v1/endpoints/reporting.py`) with authenticated access; schemas `InvoicePrintRequest`/`InvoicePrintEnvelope` in `backend/app/schemas/reporting.py`.
- Client wiring: `buildInvoicePrintEnvelope` wrapper in `frontend/js/api.js`; `createInvoicePrintPreview` structured HTML renderer in `frontend/js/print.js`; UI controls integrated into the Reports & Printing workspace (`frontend/js/reports.js`).
- Contract suite `backend/tests/test_invoice_print_envelope.py` (5 tests covering service logic, endpoint registration, schema validation and frontend integration points).
- Follows reporting/print batches 02–05 (clinical/administrative/statistical report data and print manifest); continues the "final reporting/printing integration" remaining-work item.

## Batch 86 — Receivables Aging Ledger
- Endpoint `GET /dashboard/receivables-aging` (`backend/app/api/v1/endpoints/dashboard.py`) derives outstanding balances from the Batch 82 live-payment reconciliation and classifies open invoices into stable aging buckets: 0–30, 31–60, 61–90, Over-90 days (invoice date vs aware-UTC `as_of`).
- Schemas in `backend/app/schemas/dashboard.py` expose per-bucket totals/counts plus invoice-level ledger rows (invoice number, patient, date, total, paid, balance, days outstanding, bucket).
- Client wiring: `getDashboardReceivablesAging(options)` wrapper in `frontend/js/api.js`; `createReceivablesAgingPrintPreview()` renderer (bucket summary + per-invoice ledger) in `frontend/js/print.js`; "Receivables aging ledger" card in the Reports & Printing workspace (`frontend/js/reports.js`).
- Documentation: `docs/CLIENT_RECEIVABLES_AGING_LEDGER.md` added and indexed in `docs/INDEX.md`.
- Contract suite `backend/tests/test_receivables_aging_ledger.py` (8 tests incl. clamping parity with Batches 82/85); full suite 246 passed.

## Batch 87 — Invoice Receipt Continuity Report
- Endpoint `GET /dashboard/invoice-receipt-continuity` (`backend/app/api/v1/endpoints/dashboard.py`) audits receipt-book integrity over live billing data: recent non-cancelled invoices scanned most-recent-first, receipts read in a single grouped pass over the `Payment` ledger (ordered by payment time then id; stored counters never trusted).
- Stable gap taxonomy: `missing` (live payments > 0 or partial/paid status but zero linked receipts — Batch 82 derivation parity), `duplicate` (same receipt number twice within an invoice), `sequence_break` (numeric-suffix span analysis via `_receipt_numeric_suffix`).
- Schemas `InvoiceReceiptGapItem` / `InvoiceReceiptContinuityResponse` in `backend/app/schemas/dashboard.py` expose headline aggregates (checked / with receipts / missing / duplicates / sequence breaks) plus per-invoice issue rows with expected/actual/missing counts and first/last/duplicate receipt numbers.
- Client wiring: `getDashboardInvoiceReceiptContinuity(options)` wrapper in `frontend/js/api.js`; `createInvoiceReceiptContinuityPrintPreview()` renderer (summary table + issues page with clean-book fallback) in `frontend/js/print.js`; "Invoice receipt continuity report" card in the Reports & Printing workspace (`frontend/js/reports.js`).
- Documentation: `docs/CLIENT_INVOICE_RECEIPT_CONTINUITY_REPORT.md` added and indexed in `docs/INDEX.md`.
- Contract suite `backend/tests/test_invoice_receipt_continuity_report.py` (8 tests covering endpoint wiring, live-scan semantics, gap taxonomy and span math, Batch 82 parity, schemas and frontend integration points); full suite 254 passed.

## Batch 88 — Receipt Numbering Continuity Audit
- Endpoint `GET /dashboard/receipt-numbering-continuity` (`backend/app/api/v1/endpoints/dashboard.py`) extends the Batch 87 invoice-scoped receipt audit to a whole-receipt-book audit: most recent `limit` live Payment rows with receipt numbers scanned in a single ordered pass (`payment_datetime, id`; no N+1), grouped into numeric series by non-digit prefix using the Batch 87 `_receipt_numeric_suffix` parser so both audits agree on what "numeric" means.
- Per-series findings: `missing_numbers` (skipped values between first and last issued number; detail capped at 200 while `gap_count` stays true), `duplicate_numbers` (numbers recorded more than once) and the always-holding reconciliation `expected_count == actual_count + gap_count`; non-numeric receipts are counted but never produce false gaps.
- Schemas `ReceiptSeriesGap` / `ReceiptNumberingContinuityResponse` in `backend/app/schemas/dashboard.py` expose headline aggregates (receipts checked / series / clean series / total gaps) that sum back to the scanned ledger so printed audits reconcile.
- Client wiring: `getDashboardReceiptNumberingContinuity(options)` wrapper in `frontend/js/api.js`; `createReceiptNumberingContinuityPrintPreview()` renderer (audit summary, per-series table, Missing Numbers Detail page with clean-book fallback, Duplicate Receipt Numbers table) in `frontend/js/print.js`; "Receipt numbering continuity" card in the Reports & Printing workspace (`frontend/js/reports.js`).
- Documentation: `docs/CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md` added and indexed in `docs/INDEX.md`.
- Contract suite `backend/tests/test_receipt_numbering_continuity.py` (6 tests covering endpoint wiring, single-pass scan semantics, Batch 87 parser reuse, reconciliation fields, schema exports and frontend integration points); full suite 260 passed.

## Batch 89 — Invoice Payment Reconciliation Ledger
- Endpoint `GET /dashboard/invoice-payment-reconciliation` (`backend/app/api/v1/endpoints/dashboard.py`) reconciles **every** scanned invoice against the live `Payment` ledger (not just outstanding ones as in Batches 82/86): most recent `limit` non-cancelled invoices (`invoice_date DESC, id DESC`; bounded 1–500, default 200) with payments summed in a single grouped pass (`Payment.invoice_id.in_(...)`; no N+1, stored counters/status never trusted).
- Per-row clamping keeps the Batch 68 atomic-consistency invariant intact on every printed line: `amount_paid` clamped to `total_amount`, `balance_due = max(total_amount - amount_paid, 0)` so `amount_paid + balance_due == total_amount`. New `_derive_payment_status` helper mirrors the Batch 68 taxonomy (unpaid / partial / paid boundaries: `<= 0`, `>= total`).
- Drift detection: each row carries `stored_payment_status` next to `derived_payment_status` with `is_reconciled` flagging mismatches, plus per-invoice `receipt_count`. Headline aggregates always sum back to `invoices_checked` and `total_billed == total_paid + total_outstanding`.
- Schemas `InvoicePaymentReconciliationItem` / `InvoicePaymentReconciliationResponse` in `backend/app/schemas/dashboard.py` exported in `__all__`.
- Client wiring: `getDashboardInvoicePaymentReconciliation(options)` wrapper in `frontend/js/api.js`; `createInvoicePaymentReconciliationPrintPreview()` renderer (reconciliation summary table, per-invoice ledger page, Status Drift Detail page with clean fallback) in `frontend/js/print.js`; "Invoice payment reconciliation ledger" card in the Reports & Printing workspace (`frontend/js/reports.js`).
- Regression fix (`frontend/js/reports.js`): the four newer ledger cards (aging, continuity, receipt-numbering, reconciliation) had malformed HTML attribute quoting inside the `innerHTML` template literal (`id="name\"` openers/closers), rendering invalid attributes so the `$("#...")` lookups never matched — the Prepare buttons were silently dead at runtime. All 12 ids normalized to the file's standard single-escaped form; verified with `node --check` and a Node harness that evaluates the template and confirms all 12 ids render as valid `id="..."` attributes.
- Documentation: `docs/CLIENT_INVOICE_PAYMENT_RECONCILIATION_LEDGER.md` added and indexed in `docs/INDEX.md` (catalogue count 102).
- Contract suite `backend/tests/test_invoice_payment_reconciliation_ledger.py` (7 tests covering endpoint wiring, live-scan semantics and clamp parity, status-derivation taxonomy, schema fields/exports, API wrapper, print renderer sections and Reports workspace wiring); full suite 267 passed.

## Batch 90 — Collection Summary by Patient
- Endpoint `GET /dashboard/collection-summary-by-patient` (`backend/app/api/v1/endpoints/dashboard.py`) rolls the Batch 89 reconciliation ledger up into per-patient collection totals. The invoice/payment scan was extracted into a shared `_build_reconciliation_rows(db, limit)` helper used by both endpoints (single grouped Payment pass, no N+1, stored counters never trusted; bounded 1–500, default 200), so screen feeds and print packets can never drift.
- Shared aggregation `build_collection_summary_by_patient(rows)` groups rows by patient (first-appearance order preserved), counts derived paid/partial/unpaid invoices, sums clamped billed/collected/outstanding amounts (invariant `total_collected + outstanding == total_billed` holds per patient and in headlines) and tracks `last_payment_date` from the live payment timestamps. Exported in the module `__all__` for the reporting service.
- Print envelope `POST /reports/collection-summary-print-envelope` (`backend/app/services/reporting.py`, endpoint in `backend/app/api/v1/endpoints/reporting.py`) reuses the same scan + aggregation — one implementation, two surfaces.
- Schemas: `PatientCollectionSummaryItem` / `PatientCollectionSummaryResponse` (`backend/app/schemas/dashboard.py`); `CollectionSummaryPrintRequest`, `PatientCollectionSummaryPrintLine`, `CollectionSummaryPrintData`, `CollectionSummaryPrintEnvelope` (`backend/app/schemas/reporting.py`); all exported in `__all__`.
- Client wiring: `getDashboardCollectionSummaryByPatient(options)` + `buildCollectionSummaryPrintEnvelope(payload)` wrappers in `frontend/js/api.js`; `createCollectionSummaryPrintPreview()` renderer (headlines table, per-patient collection ledger, clean empty-state fallback) in `frontend/js/print.js`; "Collection summary by patient" card with limit control in the Reports & Printing workspace (`frontend/js/reports.js`).
- Documentation: `docs/CLIENT_COLLECTION_SUMMARY_BY_PATIENT.md` added and indexed in `docs/INDEX.md` (catalogue count 103). README Reporting & Printing section and test-suite line advanced to Batch 90 / 275 tests.
- Contract suite `backend/tests/test_collection_summary_by_patient.py` (8 tests covering shared-scan endpoint semantics, print-envelope reuse, dashboard/reporting schema fields and exports, API wrappers, print renderer sections, Reports workspace wiring and documentation indexing); full suite 275 passed.

## Batch 91 — Receivables Aging Print Envelope
- Shared derivation extraction (`backend/app/api/v1/endpoints/dashboard.py`): the Batch 86 aging bucketing moved into `build_receivables_aging_result(invoices, patients, paid_by_invoice, as_of)` (exported in `__all__`); the dashboard endpoint now delegates to it, so screen feed and print packet run one implementation and can never drift. `_RECEIVABLES_BUCKETS` stays single-sourced; all four buckets always present for stable printed shape.
- Print envelope `POST /reports/receivables-aging-print-envelope` (`backend/app/services/reporting.py` + endpoint in `backend/app/api/v1/endpoints/reporting.py`): reuses the Batch 82 live-payment outstanding scan (single grouped Payment pass, no N+1, stored counters never trusted) and the shared derivation; printed rows satisfy `amount_paid + balance_due == total_amount` (Batch 68 parity), bucket counts/totals sum back to `invoice_count`/`total_outstanding`.
- Schemas: `ReceivablesAgingPrintRequest` (limit 1–500 default 200, title ≤200), `ReceivablesAgingBucketPrintLine`, `ReceivablesAgingInvoicePrintLine`, `ReceivablesAgingPrintData`, `ReceivablesAgingPrintEnvelope` (`report_type: "receivables_aging_print"`) in `backend/app/schemas/reporting.py`; all exported in `__all__`.
- Client wiring: `buildReceivablesAgingPrintEnvelope(payload)` wrapper in `frontend/js/api.js`; `createReceivablesAgingPrintPreview()` accepts `{envelope}` with backward-compatible `{data}` fallback (envelope data/title take precedence); the Reports & Printing "Receivables aging ledger" card prepares through the envelope instead of the dashboard feed, status line from envelope aggregates. Card ids verified to render as valid `id="..."` attributes via Node harness (Batch 89 quoting convention preserved).
- Documentation: `docs/CLIENT_RECEIVABLES_AGING_PRINT_ENVELOPE.md` added and indexed in `docs/INDEX.md` (catalogue count 104). README Reporting & Printing section and test-suite line advanced to Batch 91 / 282 tests.
- Contract suite `backend/tests/test_receivables_aging_print_envelope.py` (7 tests covering shared-derivation extraction, endpoint/service reuse of the live scan, print schema fields/exports, API wrapper, envelope-aware renderer, Reports workspace wiring and docs indexing); Batch 86 workspace-wiring test updated for the envelope-based card; full suite 282 passed.

## Batch 92 — Invoice Receipt Continuity Print Envelope
- Shared helper extraction (`backend/app/api/v1/endpoints/dashboard.py`): the Batch 87 continuity audit moved out of the endpoint body into `_load_continuity_scan_inputs(db, limit)` (recent non-cancelled invoice scan + patients + single grouped Payment pass collecting receipt numbers and live paid totals — no N+1, stored counters never trusted) and `build_invoice_receipt_continuity_result(...)` (pure missing/duplicate/sequence_break classification + headline aggregates). The dashboard endpoint delegates to both; screen feed and print packet run one implementation and can never drift.
- Print envelope `POST /reports/invoice-receipt-continuity-print-envelope` (`backend/app/services/reporting.py` + endpoint in `backend/app/api/v1/endpoints/reporting.py`): reuses the exact shared scan + derivation, so printed headline aggregates always sum back to `invoices_checked` exactly as on screen for the same scan window.
- Schemas: `InvoiceReceiptContinuityPrintRequest` (limit 1–500 default 200, title ≤200), `InvoiceReceiptGapPrintLine`, `InvoiceReceiptContinuityPrintData` (aggregates plus `issue_count`), `InvoiceReceiptContinuityPrintEnvelope` (`report_type: "invoice_receipt_continuity_print"`) in `backend/app/schemas/reporting.py`; all exported in `__all__`.
- Client wiring: `buildInvoiceReceiptContinuityPrintEnvelope(payload)` wrapper in `frontend/js/api.js`; `createInvoiceReceiptContinuityPrintPreview()` accepts `{envelope}` with backward-compatible `{data}` fallback (envelope data/title take precedence); the Reports & Printing "Invoice receipt continuity report" card prepares through the envelope instead of the dashboard feed, status line from envelope aggregates (`issue_count` replaces `issues.length`). Card ids verified to render as valid `id="..."` attributes via Node harness (Batch 89 quoting convention preserved).
- Documentation: `docs/CLIENT_INVOICE_RECEIPT_CONTINUITY_PRINT_ENVELOPE.md` added and indexed in `docs/INDEX.md` (catalogue count 105). README Reporting & Printing section and test-suite line advanced to Batch 92 / 289 tests.
- Contract suite `backend/tests/test_invoice_receipt_continuity_print_envelope.py` (7 tests covering shared-helper extraction, endpoint/service reuse of the live scan, print schema fields/exports, API wrapper, envelope-aware renderer with fallback, Reports workspace parity switch and docs indexing); Batch 87 workspace-wiring test updated for the envelope-based card; full suite 289 passed.

## Cleanup policy
- Transfer baselines always exclude `.git`, `.env`, Python caches/compiled files, test caches and build artifacts.
- Local `E:\HMS` cleanup removes only confirmed generated clutter unless explicitly instructed otherwise.
- Do not delete source files based only on filename similarity; confirm references first.
- Historical documentation is retained unless demonstrably obsolete, duplicated or contradicted.

## Batch 55 correction
- Batch 55 was committed with an incomplete client-only history implementation.
- Batch 56 restores the correct backend history contract and wires the client to it.
- The latest ZIP from the user remains authoritative; remote repository inspection is not used for baseline reconstruction.


## Batch 61 — IPD Bed Occupancy Concurrency
- Admission/discharge now use row locking for the affected bed/admission.
- Database partial unique index prevents more than one active admission per bed.
- Bed allocation/release remains atomic with admission/discharge.

## Batch 66 — Laboratory Result Workflow Completion
- Laboratory results use monotonic status flow: draft -> verified -> released.
- Verified/released reports require result text.
- Released reports are immutable.
- Investigation status advances to in_progress on verification and completed on release.

## Batch 64 — Pharmacy Dispensing Ledger Completion
- Dispensing now creates a corresponding `StockCard` ISSUE/`DISPENSE` entry in the same transaction as stock decrement and `DispenseRecord`.
- Expired StockBatch records are blocked from dispensing at the service layer.
- Stock-batch status endpoint exposes available/expiring/expired/exhausted states for client workflows.

## Batch 68 — Billing Atomic Consistency
- Payment creation locks the invoice row while checking and recording the outstanding balance.
- Invoice payment status is derived from payment totals and is no longer directly client-controlled through invoice update.
- Invoice items cannot be added/removed on paid or cancelled invoices.
- Item add/remove recalculates invoice total and preserves a derived unpaid/partial/paid status.
- Item deletion is blocked if the resulting invoice total would fall below the amount already paid.

## Batch 78 — Clinical Cross-Module Workflow Continuity
- Follow-up records validate `previous_prescription_id`/`next_prescription_id` lineage: the prescription must exist and belong to a visit of the same patient (enforced on create and update).
- Due-follow-up window query: service `list_due(from, to)` plus `GET /followups?due_from=&due_to=` (both-or-neither validation; `case_record_id` remains supported).
- Case-wide prescription retrieval: repository `get_by_visits`, service `get_by_case`, endpoint `GET /prescriptions/by-case/{case_record_id}` (registered before the id lookup route) spanning the case's primary visit and any visits linked back via `Visit.case_record_id`.
- Client wrappers `listDueFollowups(fromIso, toIso)` and `listCasePrescriptions(caseRecordId)` in `frontend/js/api.js`.
- Contract suite `backend/tests/test_clinical_workflow_continuity.py` (5 tests; full suite 210 passed).
- Environment note: backend venv pytest drifted to 9.x/pytest-asyncio 1.4 which broke plugin loading; reinstalled within the pinned ranges (`pytest>=8.3,<9`, `pytest-asyncio>=0.25,<1`).

## Batch 79 — Clinician Dashboard Due-Follow-up Continuity
- New endpoint `GET /dashboard/due-followups` (`backend/app/api/v1/endpoints/dashboard.py`) built on the Batch 78 `FollowUpService.list_due` window query; defaults to now → +7 days (`days_ahead` 0–365, `limit` 1–200), accepts explicit `from_datetime` to surface overdue items; SQLite naive-UTC normalisation applied to inputs.
- Each due follow-up is enriched with actionable identity: patient name/number and case number via batched `Patient`/`CaseRecord` lookups (no N+1); response schemas `DueFollowUpItem`/`DueFollowUpsResponse` in `backend/app/schemas/dashboard.py`.
- Router registered in `backend/app/api/v1/api.py` under the billing section as the clinician dashboard group.
- Client wiring: `getDashboardDueFollowups(options)` wrapper in `frontend/js/api.js`; dashboard renders a "Due follow-ups (next 7 days)" panel whose cards dispatch `hhms:open-patient-clinical` to hand off into the clinical workspace; graceful unavailable-state on fetch failure.
- Follow-up form in `frontend/js/clinical.js` now captures `next_followup_datetime` (datetime-local) and saved follow-up cards display the scheduled next visit, so due lists have data end-to-end.
- Contract suite `backend/tests/test_clinician_dashboard_due_followups.py` (7 tests; full suite 217 passed).

## Batch 82 — Dashboard Outstanding Billing Continuity
- New endpoint `GET /dashboard/outstanding-invoices` (`backend/app/api/v1/endpoints/dashboard.py`) built on `billing_service.list_outstanding_invoices`: unpaid/partial candidates only, oldest-first, balances derived from live payments so stale stored statuses and cancelled invoices never surface (`limit` 1–200).
- Per-row enrichment: patient name/number via batched lookup (no N+1), invoice number/date, `amount_paid` clamped to the invoice total, non-negative `balance_due` reconciling to `total_amount`, payment status and `days_outstanding`; aggregates `total_outstanding`, `invoice_count`, `as_of` exposed by `OutstandingInvoiceItem`/`OutstandingInvoicesResponse` in `backend/app/schemas/dashboard.py`.
- Client wiring: `getDashboardOutstandingInvoices(options)` wrapper in `frontend/js/api.js`; dashboard "Outstanding invoices" panel with count/total summary whose cards navigate to the patients view and dispatch `hhms:open-patient`; graceful unavailable-state on fetch failure.
- Documentation: `docs/CLIENT_DASHBOARD_OUTSTANDING_INVOICES.md` added and indexed in `docs/INDEX.md`.
- Contract suite `backend/tests/test_dashboard_outstanding_invoices.py` (full suite 222 passed).
