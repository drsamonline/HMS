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

Functional application build is in progress through **Batch 95 — Collection Summary Print Envelope**
(`POST /reports/collection-summary-print-envelope` builds the printable per-patient collection packet through the
exact shared scan/aggregation pair (`_build_reconciliation_rows` + `build_collection_summary_by_patient`) behind
`GET /dashboard/collection-summary-by-patient` — one implementation, two surfaces, so printed headlines always
satisfy `total_billed == total_collected + total_outstanding`; the Reports & Printing collection summary card now
prepares through the envelope. Follows Batch 94's invoice payment reconciliation print envelope
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
continuity, server/client packaging
and deployment, and completion of final reporting/printing integration. Comprehensive QA/debugging begins after
cross-module integration, packaging, and final reporting/printing are complete.
See [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md)
for the authoritative per-batch state and [CHANGELOG.md](CHANGELOG.md) for change history.
