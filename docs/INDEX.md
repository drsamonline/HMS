# HHMS Documentation Index

> Master navigation guide for all Homeopathic Hospital Management System (HHMS) documentation.

---

## Contents

1. [Core Specifications](#core-specifications)
2. [Architecture & Deployment](#architecture--deployment)
3. [Clinical Core](#clinical-core)
4. [Masters & Sequences](#masters--sequences)
5. [Pharmacy, Inventory & Billing](#pharmacy-inventory--billing)
6. [Statistics & Reporting](#statistics--reporting)
7. [RBAC & Audit](#rbac--audit)
8. [Data Lifecycle & Archival](#data-lifecycle--archival)
9. [IPD Bed Management](#ipd-bed-management)
10. [Client Workspaces](#client-workspaces)
11. [API Convergence](#api-convergence)
12. [Maintenance Audits](#maintenance-audits)
13. [Documentation Principles](#documentation-principles)
14. [Recommended Reading Order](#recommended-reading-order)
15. [Document Status Definitions](#document-status-definitions)
16. [Development Workflow](#development-workflow)

---

## Document Catalogue

### Core Specifications

| Document | Description |
|----------|-------------|
| [MASTER_SPECIFICATION.md](MASTER_SPECIFICATION.md) | Complete system specification: modules, screens, roles, workflows, reports |
| [API_SPECIFICATION.md](API_SPECIFICATION.md) | REST API design standards, endpoint organization, request/response conventions |
| [DATABASE_ENTITIES.md](DATABASE_ENTITIES.md) | Frozen business entity list with attributes and relationships |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Physical SQLite schema: tables, columns, keys, constraints, indexes |
| [GLOSSARY.md](GLOSSARY.md) | Authoritative project terminology definitions |
| [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) | Naming standards for code, database, files, and version control |
| [IMPLEMENTATION_RULES.md](IMPLEMENTATION_RULES.md) | Binding implementation rules for all development work |
| [VALIDATION_RULES.md](VALIDATION_RULES.md) | Data validation rules across clinical, statistical, and print domains |
| [PRINT_STANDARDS.md](PRINT_STANDARDS.md) | Standards for all printable reports and documents |
| [UI_GUIDELINES.md](UI_GUIDELINES.md) | Client UI stack, layout, UX, and print-interface guidelines |
| [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | Testing approach, organization, quality standards, validation process |
| [SECURITY_ARCHITECTURE.md](SECURITY_ARCHITECTURE.md) | Authentication, authorization, credential, session, and audit security |
| [MASTER_IMPLEMENTATION_PROMPT.md](MASTER_IMPLEMENTATION_PROMPT.md) | Master prompt used to drive AI-assisted implementation sessions |

### Architecture & Deployment

| Document | Description |
|----------|-------------|
| [BACKEND_ARCHITECTURE.md](BACKEND_ARCHITECTURE.md) | Backend software architecture, project organization, dependency rules |
| [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md) | LAN desktop client architecture (HTML/CSS/vanilla JS in WebView2) |
| [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) | Server/client LAN deployment topology and environment requirements |
| [SERVER_STARTUP.md](SERVER_STARTUP.md) | Server startup sequence and runtime hardening |
| [SERVER_PACKAGING.md](SERVER_PACKAGING.md) | Server EXE packaging foundation |
| [LAN_DISCOVERY.md](LAN_DISCOVERY.md) | LAN discovery of the server by clients |

### Clinical Core

| Document | Description |
|----------|-------------|
| [CLINICAL_CORE.md](CLINICAL_CORE.md) | Core clinical workflow documentation |
| [IPD_CLINICAL.md](IPD_CLINICAL.md) | IPD clinical documentation workflow |
| [CLINICAL_ACTIVITY_INTEGRATION.md](CLINICAL_ACTIVITY_INTEGRATION.md) | Clinical activity recording and integration |
| [LABORATORY_RESULT_WORKFLOW.md](LABORATORY_RESULT_WORKFLOW.md) | Laboratory result workflow (Batch 66) |
| [MRD.md](MRD.md) | Medical Records Department: patient files and archiving |
| [ENCOUNTER_INTEGRITY.md](ENCOUNTER_INTEGRITY.md) | Cross-module encounter integrity (Batch 65) |

### Masters & Sequences

| Document | Description |
|----------|-------------|
| [DEPARTMENT_MASTER.md](DEPARTMENT_MASTER.md) | Department master data management |
| [DEPARTMENT_SERVICE_ACTIVITY.md](DEPARTMENT_SERVICE_ACTIVITY.md) | Department/service and activity foundation |
| [NUMBER_SEQUENCE_INTEGRATION.md](NUMBER_SEQUENCE_INTEGRATION.md) | Number sequence integration for document identifiers |
| [OPERATIONAL_YEAR_BASIS.md](OPERATIONAL_YEAR_BASIS.md) | Calendar/financial operational-year basis |

### Pharmacy, Inventory & Billing

| Document | Description |
|----------|-------------|
| [GOODS_RECEIPT_TO_PHARMACY_STOCK.md](GOODS_RECEIPT_TO_PHARMACY_STOCK.md) | Goods receipt to pharmacy stock integration (Batch 59) |
| [PHARMACY_STOCK_CARD_LEDGER.md](PHARMACY_STOCK_CARD_LEDGER.md) | Pharmacy stock card ledger |
| [PHARMACY_DISPENSE_LEDGER_COMPLETION.md](PHARMACY_DISPENSE_LEDGER_COMPLETION.md) | Pharmacy dispensing ledger completion (Batch 64) |
| [PHARMACY_DISPENSING_STOCK_INTEGRITY.md](PHARMACY_DISPENSING_STOCK_INTEGRITY.md) | Pharmacy dispensing stock integrity |
| [PHARMACY_STOCK_SAFETY.md](PHARMACY_STOCK_SAFETY.md) | Pharmacy stock safety (Batch 60) |
| [BILLING_INTEGRITY.md](BILLING_INTEGRITY.md) | Billing integrity (Batch 67) |
| [BILLING_ATOMIC_CONSISTENCY.md](BILLING_ATOMIC_CONSISTENCY.md) | Billing atomic consistency (Batch 68) |

### Statistics & Reporting

| Document | Description |
|----------|-------------|
| [STATISTICS_ENGINE.md](STATISTICS_ENGINE.md) | Hospital statistics engine |
| [STATISTICS_REPORTING_DEDUP.md](STATISTICS_REPORTING_DEDUP.md) | Hospital statistics reporting and deduplication |
| [STATISTICS_DEPARTMENT_SERVICE_BREAKDOWN.md](STATISTICS_DEPARTMENT_SERVICE_BREAKDOWN.md) | Department and service statistics breakdown |
| [REPORTING_PRINT_DATA.md](REPORTING_PRINT_DATA.md) | Reporting and print-data foundation |
| [REPORTING_PRINT_BATCH_02.md](REPORTING_PRINT_BATCH_02.md) | Reporting & print-data Batch 02 |
| [REPORTING_PRINT_BATCH_03.md](REPORTING_PRINT_BATCH_03.md) | Reporting / print Batch 03 |
| [REPORTING_PRINT_BATCH_04.md](REPORTING_PRINT_BATCH_04.md) | Reporting / print Batch 04 |
| [REPORTING_PRINT_BATCH_05.md](REPORTING_PRINT_BATCH_05.md) | Reporting / print Batch 05 — print manifest |

### RBAC & Audit

| Document | Description |
|----------|-------------|
| [RBAC_CONSISTENCY.md](RBAC_CONSISTENCY.md) | Role-based access control consistency batch |

### Data Lifecycle & Archival

| Document | Description |
|----------|-------------|
| [DATA_LIFECYCLE_AND_MAINTENANCE.md](DATA_LIFECYCLE_AND_MAINTENANCE.md) | Data lifecycle, case renewal, and maintenance policy |
| [ARCHIVE_RETENTION_TIERS.md](ARCHIVE_RETENTION_TIERS.md) | Archive retention tiers (online, read-only, cold) |
| [HISTORICAL_DATA_ACCESS.md](HISTORICAL_DATA_ACCESS.md) | Historical archive access model |
| [UNIFIED_PATIENT_HISTORY.md](UNIFIED_PATIENT_HISTORY.md) | Unified live + historical patient history |
| [ANNUAL_CASE_ROLLOVER.md](ANNUAL_CASE_ROLLOVER.md) | Annual case rollover and archival workflow |
| [BATCH_51_DATA_LIFECYCLE_CASE_RENEWAL.md](BATCH_51_DATA_LIFECYCLE_CASE_RENEWAL.md) | Batch 51 — data lifecycle, case renewal & maintenance |
| [BATCH_56_CORRECT_PATIENT_HISTORY.md](BATCH_56_CORRECT_PATIENT_HISTORY.md) | Batch 56 — corrected unified patient history |
| [BATCH_57_HISTORICAL_EVENT_INTEGRATION.md](BATCH_57_HISTORICAL_EVENT_INTEGRATION.md) | Batch 57 — historical event integration |

### IPD Bed Management

| Document | Description |
|----------|-------------|
| [IPD_BED_OCCUPANCY_CONCURRENCY.md](IPD_BED_OCCUPANCY_CONCURRENCY.md) | IPD bed occupancy concurrency handling |

### Client Workspaces

| Document | Description |
|----------|-------------|
| [CLIENT_NATIVE_HOST.md](CLIENT_NATIVE_HOST.md) | HHMS native client host (WebView2 shell) |
| [CLIENT_CONNECTION.md](CLIENT_CONNECTION.md) | Client connection foundation |
| [CLIENT_SHELL_CONNECTION.md](CLIENT_SHELL_CONNECTION.md) | Client shell and connection integration |
| [CLIENT_AUTH_PATIENT_WORKSPACE.md](CLIENT_AUTH_PATIENT_WORKSPACE.md) | Client authentication and patient workspace |
| [CLIENT_PATIENT_WORKSPACE.md](CLIENT_PATIENT_WORKSPACE.md) | Client patient workspace (Batch 08) |
| [CLIENT_CLINICAL_CASE_WORKSPACE.md](CLIENT_CLINICAL_CASE_WORKSPACE.md) | Client clinical case workspace (Batch 09) |
| [CLIENT_CLINICAL_RECORDS.md](CLIENT_CLINICAL_RECORDS.md) | Client clinical records (Batch 10) |
| [CLIENT_INVESTIGATIONS_AND_MODULE_INTEGRATION.md](CLIENT_INVESTIGATIONS_AND_MODULE_INTEGRATION.md) | Client clinical module integration (Batch 12) |
| [CLIENT_STATISTICS_REPORTS.md](CLIENT_STATISTICS_REPORTS.md) | Client statistics and reports/printing (Batch 14) |
| [CLIENT_UNIFIED_DASHBOARD.md](CLIENT_UNIFIED_DASHBOARD.md) | Client unified dashboard and navigation (Batch 17) |
| [CLIENT_NAVIGATION_INTEGRITY.md](CLIENT_NAVIGATION_INTEGRITY.md) | Client navigation integrity (Batch 21) |
| [CLIENT_STARTUP_SESSION_RESTORE.md](CLIENT_STARTUP_SESSION_RESTORE.md) | Client startup and session restore (Batch 24) |
| [CLIENT_CLINICAL_CONTEXT_INTEGRATION.md](CLIENT_CLINICAL_CONTEXT_INTEGRATION.md) | Client clinical context integration (Batch 28) |
| [CLIENT_INVENTORY_STOCK_WORKSPACE.md](CLIENT_INVENTORY_STOCK_WORKSPACE.md) | Client inventory and stock workspace (Batch 31) |
| [CLIENT_INVESTIGATION_RESULT_FLOW.md](CLIENT_INVESTIGATION_RESULT_FLOW.md) | Client investigation result flow (Batch 35) |
| [CLIENT_ADMINISTRATION_WORKSPACE.md](CLIENT_ADMINISTRATION_WORKSPACE.md) | Client administration workspace (Batch 36) |
| [CLIENT_DESIGNATION_MASTER.md](CLIENT_DESIGNATION_MASTER.md) | Client designation master (Batch 37) |
| [CLIENT_INVENTORY_STOCK_BALANCE.md](CLIENT_INVENTORY_STOCK_BALANCE.md) | Client inventory stock balance (Batch 40) |
| [CLIENT_PROCUREMENT_WORKSPACE.md](CLIENT_PROCUREMENT_WORKSPACE.md) | Client procurement workspace (Batch 41) |
| [CLIENT_AUDIT_ACTIVITY.md](CLIENT_AUDIT_ACTIVITY.md) | Client audit and activity trail (Batch 45) |
| [CLIENT_CLINICAL_WORKFLOW_INTEGRATION.md](CLIENT_CLINICAL_WORKFLOW_INTEGRATION.md) | Client clinical workflow integration |
| [CLIENT_CLINICIAN_DASHBOARD_DUE_FOLLOWUPS.md](CLIENT_CLINICIAN_DASHBOARD_DUE_FOLLOWUPS.md) | Clinician dashboard due-follow-up continuity (Batch 79) |
| [CLIENT_DASHBOARD_OUTSTANDING_INVOICES.md](CLIENT_DASHBOARD_OUTSTANDING_INVOICES.md) | Dashboard outstanding billing continuity (Batch 82) |
| [CLIENT_DASHBOARD_BED_OCCUPANCY.md](CLIENT_DASHBOARD_BED_OCCUPANCY.md) | Dashboard IPD bed-occupancy continuity feed (Batch 83) |
| [CLIENT_DASHBOARD_PENDING_INVESTIGATIONS.md](CLIENT_DASHBOARD_PENDING_INVESTIGATIONS.md) | Dashboard laboratory pending-investigation feed (Batch 84) |
| [CLIENT_INVOICE_PRINT_ENVELOPE.md](CLIENT_INVOICE_PRINT_ENVELOPE.md) | Invoice print envelope for reporting integration (Batch 85) |
| [CLIENT_RECEIVABLES_AGING_LEDGER.md](CLIENT_RECEIVABLES_AGING_LEDGER.md) | Receivables aging ledger print feed (Batch 86) |
| [CLIENT_INVOICE_RECEIPT_CONTINUITY_REPORT.md](CLIENT_INVOICE_RECEIPT_CONTINUITY_REPORT.md) | Invoice receipt continuity audit report (Batch 87) |
| [CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md](CLIENT_RECEIPT_NUMBERING_CONTINUITY_AUDIT.md) | Receipt numbering continuity audit (Batch 88) |
| [CLIENT_OPERATIONAL_WORKSPACE_INTEGRATION.md](CLIENT_OPERATIONAL_WORKSPACE_INTEGRATION.md) | Client operational workspace integration |
| [CLIENT_OPERATIONAL_NAVIGATION_CONVERGENCE.md](CLIENT_OPERATIONAL_NAVIGATION_CONVERGENCE.md) | Client operational navigation convergence |
| [CLIENT_RBAC_NAVIGATION.md](CLIENT_RBAC_NAVIGATION.md) | Client RBAC-aware navigation |
| [CLIENT_PATIENT_TIMELINE.md](CLIENT_PATIENT_TIMELINE.md) | Client patient timeline |
| [CLIENT_OPD_QUEUE.md](CLIENT_OPD_QUEUE.md) | Client OPD queue |
| [CLIENT_OPD_QUEUE_INTEGRATION.md](CLIENT_OPD_QUEUE_INTEGRATION.md) | Client OPD queue integration |
| [CLIENT_OPD_CLINICAL_HANDOFF.md](CLIENT_OPD_CLINICAL_HANDOFF.md) | Client OPD to clinical handoff |
| [CLIENT_IPD_WORKSPACE.md](CLIENT_IPD_WORKSPACE.md) | Client IPD workspace |
| [CLIENT_IPD_MANAGEMENT.md](CLIENT_IPD_MANAGEMENT.md) | Client IPD management |
| [CLIENT_IPD_DISCHARGE.md](CLIENT_IPD_DISCHARGE.md) | Client IPD discharge |
| [CLIENT_DEPARTMENT_MASTER.md](CLIENT_DEPARTMENT_MASTER.md) | Client department and service master |
| [CLIENT_MEDICINE_BATCH_MASTER.md](CLIENT_MEDICINE_BATCH_MASTER.md) | Client medicine and batch master |
| [CLIENT_PHARMACY_WORKSPACE.md](CLIENT_PHARMACY_WORKSPACE.md) | Client pharmacy workspace |
| [CLIENT_BILLING_INVOICE_ITEMS.md](CLIENT_BILLING_INVOICE_ITEMS.md) | Client billing invoice items |
| [CLIENT_BILLING_MRD_WORKSPACE.md](CLIENT_BILLING_MRD_WORKSPACE.md) | Client billing and MRD workspace |
| [CLIENT_MRD_MEDICAL_DOCUMENTS.md](CLIENT_MRD_MEDICAL_DOCUMENTS.md) | Client MRD medical documents |
| [CLIENT_BACKUP_WORKSPACE.md](CLIENT_BACKUP_WORKSPACE.md) | Client backup workspace |
| [CLIENT_HOSPITAL_SYSTEM_SETTINGS.md](CLIENT_HOSPITAL_SYSTEM_SETTINGS.md) | Hospital and system settings workspace |
| [CLIENT_PRINT_RENDERER.md](CLIENT_PRINT_RENDERER.md) | Client print renderer |
| [CLIENT_BATCH_PRINT.md](CLIENT_BATCH_PRINT.md) | Client batch printing |
| [CLIENT_NETWORK_TIMEOUT.md](CLIENT_NETWORK_TIMEOUT.md) | Client network timeout handling |
| [CLIENT_RUNTIME_RESILIENCE.md](CLIENT_RUNTIME_RESILIENCE.md) | Client runtime resilience |
| [CLIENT_UNSAVED_CHANGES.md](CLIENT_UNSAVED_CHANGES.md) | Client unsaved-changes protection |

### API Convergence

| Document | Description |
|----------|-------------|
| [API_ROUTER_CONVERGENCE.md](API_ROUTER_CONVERGENCE.md) | API router convergence (Batch 63 correction) |

### Maintenance Audits

| Document | Description |
|----------|-------------|
| [BASELINE_CLEANUP_HMS27.md](BASELINE_CLEANUP_HMS27.md) | Baseline cleanup audit — HMS27 |
| [CLEANUP_2026-08-13.md](CLEANUP_2026-08-13.md) | Repository cleanup audit — 2026-08-13 |

---

## Documentation Principles

All HHMS documentation adheres to the following principles:

1. **Single Source of Truth** — Each concept, entity, or rule is defined in exactly one document. Other documents reference it rather than duplicate it.
2. **Specification Before Implementation** — Features, schemas, and behaviours are documented before code is written. Documentation drives development, not the reverse.
3. **Precision and Completeness** — Documents must be unambiguous, self-contained, and sufficient for a developer to implement against without verbal clarification.
4. **Living Documents** — Documentation is versioned and maintained alongside the codebase; specification changes are reflected before implementation proceeds.
5. **Consistent Structure** — All documents follow a uniform format with clear section headings and standardised terminology (see [GLOSSARY.md](GLOSSARY.md)).
6. **No Assumptions** — Requirements, constraints, and edge cases are stated explicitly; implicit knowledge is avoided.

---

## Recommended Reading Order

| Order | Document | Audience |
|-------|----------|----------|
| 1 | [INDEX.md](INDEX.md) | All |
| 2 | [MASTER_SPECIFICATION.md](MASTER_SPECIFICATION.md) | All |
| 3 | [DATABASE_ENTITIES.md](DATABASE_ENTITIES.md) | Backend, Database |
| 4 | [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Backend, Database |
| 5 | [API_SPECIFICATION.md](API_SPECIFICATION.md) | Backend |
| 6 | [BACKEND_ARCHITECTURE.md](BACKEND_ARCHITECTURE.md) | Backend |
| 7 | [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md) | Frontend |
| 8 | [UI_GUIDELINES.md](UI_GUIDELINES.md) | Frontend |
| 9 | [SECURITY_ARCHITECTURE.md](SECURITY_ARCHITECTURE.md) | All developers |
| 10 | [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | All developers |

- **Stakeholders and product owners** — focus on the Master Specification and [ROADMAP.md](../ROADMAP.md).
- **Backend developers** — read all core specifications, with particular attention to Database Entities and Schema.
- **Frontend developers** — prioritise the Master Specification, Frontend Architecture, and UI Guidelines.
- **Reviewers** — must be familiar with all documents to evaluate compliance during code review.

---

## Document Status Definitions

Every HHMS document carries a status indicator:

| Status | Definition |
|--------|------------|
| **Draft** | Under initial creation. Content is incomplete. Must not be used as a basis for implementation. |
| **Under Review** | Complete and awaiting team review. Content may change based on feedback. |
| **Approved** | Passed review and accepted as the current specification. Implementation may proceed. |
| **Active** | Current authoritative source. All implementation and decisions must align with it. |
| **Deprecated** | Superseded or no longer relevant. Retained for historical reference only. |
| **Archived** | Preserved for audit and historical purposes. Not applicable to the current project state. |

---

## Development Workflow

All HHMS development follows a strict sequential workflow. No step may be skipped or performed out of order:

```text
Specification → Review → Implementation → Code Review → Testing → Git Commit → Next Milestone
```

1. **Specification** — Write or update the relevant documentation to fully describe the feature, entity, or change, including acceptance criteria.
2. **Review** — Resolve gaps and ambiguities; documentation must be approved before implementation begins.
3. **Implementation** — Code strictly according to the approved specification, following [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) and [IMPLEMENTATION_RULES.md](IMPLEMENTATION_RULES.md). No scope creep.
4. **Code Review** — Verify compliance with the specification, coding standards, and architectural patterns using [.ai/REVIEW_CHECKLIST.md](../.ai/REVIEW_CHECKLIST.md).
5. **Testing** — Test against the acceptance criteria (unit, integration, and manual verification). All tests must pass.
6. **Git Commit** — Commit following the established conventions, referencing the relevant specification document and milestone.
7. **Next Milestone** — Update progress tracking and begin the next milestone's specification phase.

---

*101 documents catalogued · See also: [README.md](../README.md) · [CHANGELOG.md](../CHANGELOG.md) · [ROADMAP.md](../ROADMAP.md) · [CONTRIBUTING.md](../CONTRIBUTING.md) · [SECURITY.md](../SECURITY.md)*
