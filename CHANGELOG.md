# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Sessions are listed newest-first within each release; batch entries reflect the
functional build batches tracked in [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md).

## [Unreleased]

### Added — Batch 85 · Invoice Print Envelope for Reporting Integration
- Service `ReportingService.build_invoice_print_envelope` (`backend/app/services/reporting.py`) assembles a printable invoice packet: header identity, line items and totals with live payment-derived balances — `amount_paid` clamped to the invoice total, non-negative `balance_due`, reconciliation `paid + balance == total` mirroring the Batch 68 atomic-consistency invariants.
- New endpoint `POST /reports/invoice-print-envelope` (`backend/app/api/v1/endpoints/reporting.py`) with authenticated access; schemas `InvoicePrintRequest`/`InvoicePrintEnvelope` and supporting item models in `backend/app/schemas/reporting.py`.
- Client wiring: `buildInvoicePrintEnvelope` wrapper in `frontend/js/api.js`; `createInvoicePrintPreview` structured HTML renderer (invoice details, line items, totals and receipts) in `frontend/js/print.js`; UI controls integrated into the Reports & Printing workspace (`frontend/js/reports.js`).
- Continues the final reporting/printing integration track after print batches 02–05 (report data, catalog and print manifest).
- Contract test suite `backend/tests/test_invoice_print_envelope.py` (5 tests covering service logic, endpoint registration, schema validation and frontend integration points); full suite 238 passed.

### Added — Batch 84 · Laboratory Pending-Investigation Dashboard Feed
- New endpoint `GET /dashboard/pending-investigations` (`backend/app/api/v1/endpoints/dashboard.py`) surfacing the live laboratory backlog: `Investigation` rows with `is_current_year=true` and status `pending`/`in_progress` (the exact open-order pair of the Batch 66 result workflow — released reports become `completed`, cancellations never surface), ordered oldest-first by `requested_datetime` so ageing orders rise to the top.
- Per-row enrichment: patient name/number via batched lookup (no N+1), investigation number/name/status, OPD/IPD encounter lineage (`case_type`/`visit_id`/`admission_id`), requester and naive-UTC-normalised `age_hours` clamped non-negative; headline `pending_count`/`in_progress_count` aggregates and aware-UTC `as_of` exposed by schemas `PendingInvestigationItem`/`PendingInvestigationsResponse` in `backend/app/schemas/dashboard.py`.
- Client wiring: `getDashboardPendingInvestigations(options)` wrapper in `frontend/js/api.js`; dashboard "Pending investigations" panel with pending/in-progress summary whose cards navigate to the patients view and dispatch `hhms:open-patient-clinical` for direct clinical-workspace handoff; empty state and graceful unavailable-state on fetch failure mirroring the sibling panels.
- Documentation: [docs/CLIENT_DASHBOARD_PENDING_INVESTIGATIONS.md](docs/CLIENT_DASHBOARD_PENDING_INVESTIGATIONS.md) added and indexed; ROADMAP and project state advanced to Batch 84.
- Contract test suite `backend/tests/test_dashboard_pending_investigations.py` (6 tests incl. Batch 66 workflow regression lock and route-registration check); full suite 233 passed.

### Added — Batch 83 · IPD Bed-Occupancy Continuity
- New endpoint `GET /dashboard/bed-occupancy` (`backend/app/api/v1/endpoints/dashboard.py`) reconciling every active bed marked occupied/reserved against its live admission (status pair `admitted`/`active`, mirroring the Batch 61 concurrency guard): ward-ordered feed, batched admission/patient enrichment (no N+1), per-row `length_of_stay_days` from naive-UTC-normalised admission datetime, and drift visibility — beds whose occupancy flag has no matching active admission are still reported with `has_active_admission=false` instead of silently disappearing.
- Response schemas `BedOccupancyItem`/`BedOccupancyResponse` in `backend/app/schemas/dashboard.py` expose bed identity (number/ward/room/type), admission lineage (id/number/datetime/status), patient name/number and headline `occupied_count`/`total_beds` aggregates with an aware-UTC `as_of`.
- Client wiring: `getDashboardBedOccupancy(options)` wrapper in `frontend/js/api.js`; dashboard "IPD bed occupancy" panel with occupied-of-total summary whose reconciled cards navigate to the patients view and dispatch `hhms:open-patient-clinical` for direct ward handoff; drift rows render a check-IPD-records notice and are disabled; graceful unavailable-state on fetch failure.
- Documentation: [docs/CLIENT_DASHBOARD_BED_OCCUPANCY.md](docs/CLIENT_DASHBOARD_BED_OCCUPANCY.md) added and indexed; ROADMAP and project state advanced to Batch 83.
- Contract test suite `backend/tests/test_dashboard_bed_occupancy.py` (5 tests, incl. Batch 61 guarantee regression locks); full suite 227 passed.

### Added — Batch 82 · Dashboard Outstanding Billing Continuity
- New endpoint `GET /dashboard/outstanding-invoices` (`backend/app/api/v1/endpoints/dashboard.py`) built on the billing service's oldest-first outstanding feed: unpaid/partial candidates only, balances derived from live payments (stale stored statuses and cancelled invoices never surface), `limit` 1–200 with authenticated access.
- Response enrichment per row: patient name/number via batched lookup (no N+1), invoice number/date, total/amount-paid/balance-due reconciliation (`balance_due + amount_paid == total_amount`, clamped non-negative), payment status and `days_outstanding`; aggregate `total_outstanding`, `invoice_count` and `as_of` exposed by schemas `OutstandingInvoiceItem`/`OutstandingInvoicesResponse` in `backend/app/schemas/dashboard.py`.
- Client wiring: `getDashboardOutstandingInvoices(options)` wrapper in `frontend/js/api.js`; dashboard "Outstanding invoices" panel with count/total summary line whose cards navigate to the patients view and dispatch `hhms:open-patient` for direct receivables chase-up, graceful unavailable-state on fetch failure.
- Documentation: [docs/CLIENT_DASHBOARD_OUTSTANDING_INVOICES.md](docs/CLIENT_DASHBOARD_OUTSTANDING_INVOICES.md) added and indexed; ROADMAP and project state advanced to Batch 82.
- Contract test suite `backend/tests/test_dashboard_outstanding_invoices.py`; full suite 222 passed.

### Added — Batch 79 · Clinician Dashboard Due-Follow-up Continuity
- New endpoint `GET /dashboard/due-followups` turning the Batch 78 due-window service query into an actionable clinician feed: defaults to now → +7 days (`days_ahead` 0–365, `limit` 1–200), explicit `from_datetime` supported to surface overdue follow-ups; naive-UTC normalisation for SQLite comparisons.
- Response enrichment with patient name/number and case number via batched lookups (schemas `DueFollowUpItem`/`DueFollowUpsResponse` in `backend/app/schemas/dashboard.py`); router registered in `backend/app/api/v1/api.py`.
- Client wiring: `getDashboardDueFollowups(options)` wrapper in `frontend/js/api.js`; dashboard "Due follow-ups (next 7 days)" panel whose cards dispatch `hhms:open-patient-clinical` for direct handoff into the clinical workspace, with graceful unavailable-state on fetch errors.
- Follow-up form in `frontend/js/clinical.js` captures `next_followup_datetime` and follow-up cards display the scheduled next visit, closing the data-capture loop behind due lists.
- Contract test suite `backend/tests/test_clinician_dashboard_due_followups.py` (7 tests; full suite 217 passed).

### Added — Batch 78 · Clinical Cross-Module Workflow Continuity
- Follow-up prescription lineage validation: `previous_prescription_id`/`next_prescription_id` must exist and belong to a visit of the same patient; enforced on both create and update in `app/services/followup.py` (closes a referential-integrity gap where arbitrary prescription IDs could be linked across patients).
- Due-follow-up workflow surface: service `FollowUpService.list_due(from, to)` ordered by scheduled datetime, exposed via `GET /followups?due_from=&due_to=` (both parameters required together; `case_record_id` query retained).
- Case-wide prescription continuity: repository `get_by_visits`, service `get_by_case` (spans the case's primary visit plus visits linked back via `Visit.case_record_id`) and endpoint `GET /prescriptions/by-case/{case_record_id}`, registered before the id lookup route.
- Client API wrappers `listDueFollowups(fromIso, toIso, options)` and `listCasePrescriptions(caseRecordId)` in `frontend/js/api.js`.
- Contract test suite `backend/tests/test_clinical_workflow_continuity.py` (5 tests; full suite 210 passed).
- Fixed development environment drift: reinstalled pytest/pytest-asyncio within the pinned ranges after pytest 9.x broke plugin loading (`Marks cannot be applied to fixtures`).

### Added — Batch 77 · Prescription Annual Lifecycle & Lineage Rollover
- Prescription and PrescriptionItem lifecycle metadata (`prescription_year`, `item_year`, `storage_tier`, `is_current_year`) derived from the prescription datetime at creation; migration `0028_prescription_operational_year_lifecycle` backfills existing rows and makes `Prescription.visit_id` nullable so prescriptions survive visit rollover with detached lineage.
- Permanent `PrescriptionArchiveReference` and `PrescriptionItemArchiveReference` records so prescription identity, visit lineage and dispensing pointers survive physical live-database removal (closes the integrity gap where visits were archived but prescriptions had no lifecycle).
- Annual rollover now physically archives completed-year prescriptions and items before visits (preview counts `prescription_count`/`prescription_item_count`, references-before-delete, live `DispenseRecord.prescription_item_id` and `FollowUp.previous/next_prescription_id` detach, post-rollover validation keys `prescriptions_archived`/`prescription_items_archived`).
- Historical archived prescription read endpoints `/maintenance/archives/{year}/patients/{patient_id}/prescriptions|prescription-items` and client wrappers `getHistoricalArchivePrescriptions`, `getHistoricalArchivePrescriptionItems`; legacy pre-Batch-77 archive files fall back to a lineage-free dispense read so historical pharmacy history stays visible.
- Read schemas (`PrescriptionRead`, `PrescriptionItemRead`) expose lifecycle fields; `PrescriptionRead.visit_id` is now optional.
- Contract test suite `backend/tests/test_prescription_archive_rollover.py` (8 tests; full suite 203 passed).

### Added — Batch 76 · Procurement & Inventory Annual Lifecycle & Rollover
- PurchaseOrder, GoodsReceipt, StockTransaction and StockCard lifecycle metadata (`order_year`, `receipt_year`, `transaction_year`, `storage_tier`, `is_current_year`) derived from the document date at creation; migration `0027_procurement_inventory_operational_year_lifecycle` backfills existing rows.
- Permanent `PurchaseOrderArchiveReference`, `GoodsReceiptArchiveReference`, `StockTransactionArchiveReference` and `StockCardArchiveReference` records so procurement/inventory identity survives physical live-database removal.
- Annual rollover now physically archives completed-year purchase orders, goods receipts, stock transactions and stock-card ledger entries (preview counts `purchase_order_count`/`goods_receipt_count`/`stock_transaction_count`/`stock_card_count`, references-before-delete, post-rollover validation). Master data (Supplier, Medicine, InventoryItem) and live StockBatch balances are intentionally never rolled over.
- Historical archived procurement/inventory read endpoints `/maintenance/archives/{year}/purchase-orders|goods-receipts|stock-transactions|stock-cards` (administrator-only, year-scoped because these records carry no patient lineage) and client wrappers `getHistoricalPurchaseOrders`, `getHistoricalGoodsReceipts`, `getHistoricalStockTransactions`, `getHistoricalStockCards`.
- Read schemas (`PurchaseOrderRead`, `GoodsReceiptRead`, `StockTransactionRead`, `StockCardRead`) expose lifecycle fields.
- Contract test suite `backend/tests/test_procurement_archive_rollover.py` (7 tests; full suite 195 passed).

### Fixed — FastAPI 204 response-model route registration error
- `DELETE /maintenance/backups/{name}` and `DELETE /billing/invoice-items/{item_id}` declared a `None` return annotation that FastAPI turned into an implicit response model, raising `AssertionError: Status code 204 must not have a response body` at application startup. Both routes now declare `response_model=None` explicitly; the app boots cleanly (206 routes registered).

### Added — Batch 75 · MRD Annual Lifecycle & Rollover
- MedicalDocument lifecycle metadata (`document_year`, `storage_tier`, `is_current_year`) derived from the document date at creation; migration `0026_mrd_operational_year_lifecycle` backfills existing rows.
- Permanent `MedicalDocumentArchiveReference` records so document identity and visit/admission lineage survive physical live-database removal.
- Annual rollover now physically archives completed-year medical documents (preview count, references-before-delete, post-rollover validation) with result key `documents_archived`.
- Historical archived MRD read endpoint `/maintenance/archives/{year}/patients/{patient_id}/documents` and client wrapper `getHistoricalArchiveDocuments`; `MedicalDocumentRead` schema exposes lifecycle fields.

### Added — Batch 73 · IPD Annual Lifecycle & Rollover
- Admission lifecycle metadata (`admission_year`, `storage_tier`, `is_current_year`) derived from the admission datetime at creation; migration `0024_ipd_operational_year_lifecycle` backfills existing rows.
- Permanent `AdmissionArchiveReference` records so admission identity survives physical live-database removal.
- Annual rollover now physically archives completed-year admissions (preview count, references-before-delete, investigation detach, post-rollover validation) and exposes historical reads via `/maintenance/archives/{year}/patients/{patient_id}/admissions`.

### Added — Batch 74 · Laboratory Annual Lifecycle & Rollover
- Investigation/result lifecycle metadata (`investigation_year`, `result_year`, `storage_tier`, `is_current_year`) derived at creation; migration `0025_lab_operational_year_lifecycle` backfills existing rows.
- Permanent `InvestigationArchiveReference` records preserving visit/admission lineage after archival.
- Annual rollover physically archives completed-year investigations with their results; historical reads exposed via `/maintenance/archives/{year}/patients/{patient_id}/investigations` and client wrapper `getHistoricalArchiveInvestigations`.


### Added — Batch 72 · Pharmacy Annual Lifecycle & Rollover
- Dispense lifecycle metadata (`dispense_year`, `storage_tier`, `is_current_year`) derived from the dispense date at creation, honoring the configured operational year.
- Alembic migration `0023_pharmacy_operational_year_lifecycle` with backfill of existing dispense rows; `DispenseRecord.prescription_item_id` made nullable so archived links detach safely.
- Permanent `DispenseArchiveReference` records so dispense identity survives physical live-database removal.
- Annual rollover now physically archives completed-year dispense records alongside cases, visits and billing (references created before deletion, post-rollover validation extended to pharmacy).
- Historical archived pharmacy read endpoint `/maintenance/archives/{year}/patients/{patient_id}/dispenses` (joined through prescription lineage) and client API wrapper `getHistoricalArchiveDispenses`.
- `DispenseRead` schema exposes lifecycle fields.
- Contract test suite `backend/tests/test_pharmacy_archive_rollover.py` (8 tests; full suite 165 passed).

### Added — Batch 71 · Billing Annual Lifecycle & Rollover
- Invoice and payment lifecycle metadata (`invoice_year`, `payment_year`, `storage_tier`, `is_current_year`) derived from the billing date at creation, honoring the configured operational year.
- Alembic migration `0022_billing_operational_year_lifecycle` with backfill of existing invoice/payment rows; `Payment.invoice_id` made nullable so archived links detach safely.
- Permanent `InvoiceArchiveReference` and `PaymentArchiveReference` records so billing identity survives physical live-database removal.
- Annual rollover now physically archives completed-year invoices and payments alongside cases and visits (child payments detached from archived invoices first, post-rollover validation extended to billing).
- Historical archived billing read endpoints `/maintenance/archives/{year}/patients/{patient_id}/invoices|payments` and client API wrappers `getHistoricalArchiveInvoices` / `getHistoricalArchivePayments`.
- Read schemas expose lifecycle fields on `InvoiceRead` / `PaymentRead`.
- Contract test suite `backend/tests/test_billing_archive_rollover.py` (8 tests; full suite 157 passed).

### Added — Batch 70 · Encounter Annual Lifecycle & Rollover
- Visit lifecycle metadata (`visit_year`, `storage_tier`, `is_current_year`) derived from the encounter date at creation, honoring the configured operational year.
- Alembic migration `0021_visit_operational_year_lifecycle` with backfill of existing visit rows.
- Permanent `VisitArchiveReference` records so visit identity survives physical live-database removal.
- Annual rollover now physically archives completed-year visits alongside cases (children detached first, post-rollover validation extended to visits).
- Historical archived-visit read endpoint `/maintenance/archives/{year}/patients/{patient_id}/visits` and client API wrapper `getHistoricalArchiveVisits`.
- Contract test suite `backend/tests/test_visit_archive_rollover.py` (7 tests; full suite 149 passed).

### Added — Batch 69 · Annual Case Rollover
- Verified pre-rollover backup and administrator-only annual case rollover.
- Permanent `CaseArchiveReference` records for cases physically removed from the live database.
- Archived-case lineage preserved through `case_family_id` and the verified annual archive snapshot.
- Safe removal of direct case children (`Diagnosis`, `FollowUp`) before removing archived `CaseRecord` rows.
- Live `renewed_from_case_id` references cleared when they would point at physically archived cases.
- Rollover preview and execution API endpoints.
- Rollover action in the System Health & Data Lifecycle workspace.
- See [docs/ANNUAL_CASE_ROLLOVER.md](docs/ANNUAL_CASE_ROLLOVER.md).

## [0.0.1] - 2025-01-30

Foundation phase (Milestone 0) — repository initialization, standards, specification, and database design.

### Added — Session 004 · Database Schema Design (DB-002)
- [docs/DATABASE_ENTITIES.md](docs/DATABASE_ENTITIES.md) — frozen entity list with 35 entities.
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) — complete relational database schema.
- All 35 tables defined with columns, primary keys, foreign keys, and indexes.
- `snake_case` naming throughout; `created_at`/`updated_at` on all tables; `is_active` only on master/configuration tables.
- No circular dependencies; ~3NF normalization achieved.
- Module breakdown: Core 3 · Patients 2 · Clinical 3 · Prescription 2 · Pharmacy 3 · Inventory 6 · Billing 3 · IPD 6 · MRD 2 · Administration 2 · Settings 3.

### Added — Session 004 · Master Specification Finalized (SPEC-001-FINAL)
- Master Specification finalized in compact format (~8–10 pages equivalent):
  one-paragraph purpose, simplified scope lists, 12 modules (≤4 bullets each),
  12-item navigation menu, screens by module, one-line role descriptions,
  report and print-document lists, future-version feature list.
- Milestone 0 marked COMPLETE (100%).

### Added — Session 003 · Master Specification (SPEC-001)
- [docs/MASTER_SPECIFICATION.md](docs/MASTER_SPECIFICATION.md) — complete scope definition for HHMS v1.0:
  project purpose and objectives, scope boundaries (included/excluded),
  12 modules with purposes and functions, navigation structure,
  full screen inventory (60+ screens), database entity list (27 entities),
  8 major workflows, 6 user roles, report catalog (8 categories, 30+ reports),
  printable documents list, and a "Planned After Version 1" section (10 feature categories).
- Scope officially **FROZEN** for Version 1.0.

### Added — Session 002 · Repository Standardization (FND-002)
- Directory structure:
  `.github/ISSUE_TEMPLATE/`, `docs/` subfolders (01_Project → 10_Release_Notes),
  `backend/app/`, `backend/tests/`, `frontend/src/`, `frontend/public/`,
  `database/schema/`, `database/migrations/`, `scripts/setup/`, `scripts/backup/`,
  `assets/logos/`, `assets/icons/`, `assets/screenshots/`,
  `templates/print/`, `templates/reports/`, `tools/dev/`.
- Documentation standards:
  [docs/INDEX.md](docs/INDEX.md), [docs/GLOSSARY.md](docs/GLOSSARY.md),
  [docs/NAMING_CONVENTIONS.md](docs/NAMING_CONVENTIONS.md),
  [docs/UI_GUIDELINES.md](docs/UI_GUIDELINES.md),
  [docs/PRINT_STANDARDS.md](docs/PRINT_STANDARDS.md),
  [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md).
- AI governance: `.ai/PROJECT_INDEX.md`, `.ai/MODULE_STATUS.md`.

### Added — Session 001 · Repository Initialization (FND-001)
- Initial directory structure (11 root folders).
- Root documentation: `README.md`, `LICENSE` (MIT), `CHANGELOG.md`, `ROADMAP.md`
  (8 milestones, 0–7), `CONTRIBUTING.md`, `SECURITY.md`, `VERSION` (0.0.1),
  `.gitignore`, `.editorconfig`.
- AI context files in `.ai/`: project constitution (12 locked principles),
  coding rules, decisions, state tracking, review checklist, prompts.

### Changed
- `.ai/` session-tracking files (PROJECT_STATE, PROGRESS, TODO, SESSION_LOG)
  updated after each session to reflect current status.
