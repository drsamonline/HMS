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
- [x] Performance/security audit (Batch 109 — login brute-force rate limiter with structured 429 + Retry-After, SQL-level pagination gates, sub-second health probes, JWT audit invariants; 20-test QA suite)
- [x] Backup/restore and recovery hardening (Batch 108 — full round-trip verified on file-backed runtime: point-in-time restore, snapshot hygiene, corrupt-upload rejection, byte-exact downloads, admin gating)

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

## Milestone 6 – Testing ✅

- [x] Unit test suite expansion
- [x] Integration tests across modules
- [x] End-to-end tests
- [x] Multi-client LAN tests (Batch 104 — shared file-backed SQLite/WAL concurrency suite over the full ASGI stack)
- [x] Performance testing
- [x] Clean-machine installation testing (Batch 104 — fresh-directory migration-chain bootstrap, 0001→0028, verified green)

## Milestone 7 – Release 🔶 (in progress — Batches 105–109 landed packaging, EXE build, installer & CI, backup/restore + client launcher, performance & security audit)

- [x] Client launcher packaging verification (Batch 108 — `client/HHMS.Client` single-file self-contained win-x64 `HHMS-Client.exe` contract locked by QA; WebView2 SDK pinned at 1.0.3856.49; frontend bundled; `-IncludeClient` installer switch) *(offline WebView2 redistributable CAB bundling pending)*
- [ ] WebView2 runtime packaging *(launcher prerequisite check in `scripts/deploy/server-launch.ps1` done Batch 105; pinned SDK ships in the launcher EXE per Batch 108; offline redistributable bundling pending)*
- [x] Final server EXE packaging (Batch 106 — real one-file PyInstaller build executed + frozen first-run smoke verified; Batch 107 — Windows EXE automated in CI; Batch 108 — client launcher verification closed)
- [x] Installer & release automation (Batch 107 — `scripts/deploy/build-installer.ps1` Inno Setup/NSIS + `.github/workflows/release.yml` tag-triggered pipeline with SHA-256 checksums and GitHub Release publishing; Batch 108 — `-IncludeClient` launcher bundling)
- [x] Backup / restore workflows (Batch 108 — round-trip, snapshot hygiene, corrupt-upload rejection, admin gating verified on file-backed runtime)
- [x] Performance & security audit pass (Batch 109 — login brute-force rate limiter `app/middleware/rate_limit.py` with structured 429 + `Retry-After` before Argon2 work, settings-tunable budget/window, SQL-level pagination gates, sub-second health probes, JWT audit invariants; 20-test QA suite)
- [ ] Documentation finalization
- [x] Deployment scripts (Batch 105 — `scripts/deploy/`: build-server.sh, install-first-run.sh, server-launch.ps1, usage README; syntax/integrity verified by QA suite)
- [ ] User training materials
- [ ] Production release *(secret rotation required first: `data/secret.key` exists in git history through Batch 104-era commits)*

---

## Current Position

Functional application build is complete through **Batch 102 — Investigation Billing Reconciliation Feed & Print Envelope**;
**Milestone 6 Comprehensive QA is now COMPLETE (Batches 103–104)**. Batch 103 delivered the shared
full-stack QA harness (`backend/tests/_qa_harness.py` — in-memory SQLite + real middleware/auth/service/DB layers) and the
end-to-end route suite `tests/test_batch103_qa_end_to_end.py` (10 tests: auth lifecycle incl. a login-500 product bug found
and fixed — `user.hashed_password` → `user.password_hash`; patient writes with sequence minting and text normalization;
handled-error paths for missing number sequences; all 14 dashboard feeds answering 200 on cold state), the cross-module
integration suite `tests/test_batch103_cross_module_integration.py` (patient → visit → OPD token → queue progression chains
plus warm-state probes of all 14 audit feeds), and a performance smoke benchmark (~104 writes/s, 14 dashboard feeds in
102.5 ms total). Batch 104 closed the remaining Milestone 6 scope: multi-client LAN testing
(`tests/test_batch104_multi_client_lan_qa.py`, 5 tests — concurrent logins/registrations/token mints across independent
clients on one shared file-backed WAL SQLite DB plus UDP discovery handshake) and clean-machine installation testing
(`tests/test_batch104_clean_install_simulation.py`, 5 tests — fresh-directory alembic bootstrap 0001→0028, ORM-schema parity,
idempotent re-run, end-to-end auth on an empty install). Batch 104 surfaced and fixed three release-blocking defects:
(a) StaticPool was applied to *all* SQLite URLs, deadlocking any concurrent workload on the packaged file-based runtime —
now restricted to `:memory:` with QueuePool + WAL/busy_timeout for file DBs; (b) migration-chain gaps that made fresh
installs fail (missing base tables in 0018, invalid ALTER patterns in 0007/0015, partial-index syntax in 0019, 184 columns
across 15 migrations missing `CURRENT_TIMESTAMP` server defaults); (c) an `asyncio.Lock` loop-binding defect in the number
sequence service under concurrent request loops. Full backend suite reached **403 passed**; Milestone 6 closed.
**Batch 105 (Milestone 7 part 1) then landed release-packaging infrastructure**: single-source versioning from the root
`VERSION` file resolved across source/packaged/PyInstaller-frozen layouts (`backend/app/release_version.py`, surfaced by
`/health`), frozen-runtime Alembic via a bundled PyInstaller runtime hook + updated `HHMS-Server.spec`, deployment scripts
(`scripts/deploy/`: build-server.sh, install-first-run.sh, Windows server-launch.ps1 with WebView2 prerequisite check), an
18-test packaging QA suite, and completed secret-hygiene (334 stale tracked runtime/cache artifacts untracked; `.gitignore`
hardened). Full backend suite: **421 passed**. **Batch 106 (Milestone 7 part 2)** then executed the real
PyInstaller build end-to-end on Linux and smoke-tested the frozen binary against a fresh application root, fixing five
build/runtime defects (`--specpath` misuse, spec `__file__` → `SPECPATH`, project-root off-by-one, one-file artifact path,
and lazy-DBAPI `aiosqlite`/`sqlite3` hidden imports); 8-test tiered QA suite; full suite **427 passed, 2 skipped**.
**Batch 107 (Milestone 7 part 3)** added the Windows installer builder `scripts/deploy/build-installer.ps1` (Inno Setup
preferred with NSIS fallback, user-writable/no-admin install layout, patient data preserved across uninstall per the
Batch 104 relocation contract, version from the single-source `VERSION` file) and the CI release pipeline
`.github/workflows/release.yml` (test-gated Linux bundle + Windows EXE/installer jobs + SHA-256-checksummed GitHub
Release on `v*` tags), locked in by a 10-test QA suite. Full backend suite: **437 passed, 2 skipped**.
**Batch 108 (Milestone 7 part 4)** verified the backup/restore/recovery workflows end-to-end on a file-backed SQLite
runtime (point-in-time restore fidelity, pre-restore snapshot hygiene, corrupt-upload rejection, byte-exact downloads,
administrator gating on every verb) and locked the client launcher packaging contract (`HHMS-Client.exe`: single-file
self-contained win-x64 publish, WebView2 SDK pinned at 1.0.3856.49, bundled frontend, UDP discovery bridge, version in
lock-step with root `VERSION`), adding an opt-in `-IncludeClient` switch to the installer script for both Inno and NSIS
paths; 11-test QA suite. Full backend suite: **448 passed, 2 skipped**.
**Batch 109 (Milestone 7 part 5)** closed the performance & security audit: `POST /api/v1/auth/login` gained a
dependency-free sliding-window brute-force throttle (`app/middleware/rate_limit.py`, mounted outermost; structured 429 +
`Retry-After` before any Argon2 work; `LOGIN_RATE_LIMIT_ATTEMPTS`/`LOGIN_RATE_LIMIT_WINDOW_SECONDS` settings), SQL-level
pagination bounds and sub-second health-probe gates were locked by QA alongside JWT audit invariants (reserved-claim
refusal, expiry/tamper rejection, HS256 pinning, secret entropy guard); 20-test QA suite. Full backend suite:
**468 passed, 2 skipped**. Remaining
Milestone 7 scope: WebView2 offline redistributable CAB bundling,
documentation/training finalization, production release (secret rotation first — `data/secret.key` persists in git
history). Next batch: **Batch 110 — documentation/training finalization**. Batch 102 itself (third mega-batch under
the amended D-008 policy: `GET /dashboard/investigation-billing-reconciliation` proves every open
lab order from the Batch 84 pending-investigation vocabulary still carries its billed amount on a live non-cancelled invoice —
billed amounts re-derived from `InvoiceItem` line totals in one grouped pass (`billed_amount == charged_total - credited_total`,
`pending_count + in_progress_count == total_investigations_checked`, `billed_count + billed_missing_count ==
total_investigations_checked`) via the shared `build_investigation_billing_reconciliation_scan`/`_result` trio, printable
through `POST /reports/investigation-billing-reconciliation-print-envelope` with screen/paper parity by construction; the
commit also restores the Batch 100 discharge-audit/OPD-queue print envelope service builders and locks the refund-audit
rollup to scan order (no silent re-sort) lost in an incomplete merge). **Batch 102 closed the remaining functional
surfaces; Milestone 6 Comprehensive QA is complete (Batches 103–104, 403 tests green). The next batch is Batch 105 —
Milestone 7 release packaging & deployment (WebView2 runtime, final EXE packaging, deployment scripts, training
materials).** Follows Batch 101's Ward Occupancy Print Envelope & Operational Print Completion
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
