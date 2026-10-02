# HHMS Project State

## Authoritative baseline
- Baseline: latest user-supplied full ZIP (`HMS(5).zip`), superseding all older ZIP baselines.
- Latest completed functional milestone: Batch 82 — Outstanding Billing Continuity.
- Current milestone: Batch 82 (annual lifecycle complete for case, visit, billing, pharmacy, prescription lineage, IPD, laboratory, MRD, procurement and inventory domains; follow-up/prescription continuity surfaces landed; due-follow-up and outstanding-invoice workflow feeds wired into the client dashboard).
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

## Batch 82 — Outstanding Billing Continuity
- `BillingService.list_outstanding_invoices(db, limit)` returns oldest-first unpaid/partial invoices with balances derived from live `Payment` totals (stale stored statuses and cancelled rows never surface) plus the aggregate receivable total.
- New endpoint `GET /dashboard/outstanding-invoices` (`backend/app/api/v1/endpoints/dashboard.py`) enriches each row with patient name/number, per-row paid/balance reconciliation and `days_outstanding`; schemas `OutstandingInvoiceItem`/`OutstandingInvoicesResponse` in `backend/app/schemas/dashboard.py`.
- Client wiring: `getDashboardOutstandingInvoices(options)` wrapper in `frontend/js/api.js`; dashboard "Outstanding invoices" panel renders total outstanding and dispatches `hhms:open-patient` for direct handoff into the patient workspace, with graceful unavailable-state on fetch errors.
- Contract suite `backend/tests/test_dashboard_outstanding_invoices.py` (5 tests; full suite 222 passed).
- Housekeeping: `.gitignore` extended (bytecode, env files, IDE dirs, logs); tracked `__pycache__`/`*.pyc` artifacts restored to HEAD state so only intentional changes remain staged.
