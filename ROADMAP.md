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
- [x] Seed data creation (final pass) *(Batch 117 — verified: v1.0 ships a clean-install database by design; reference/master data is created through the application UI and bootstrapped at first run, while QA suites seed deterministic fixtures via `backend/tests/_qa_harness.py`. No production seed dataset is required for release.)*

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
- [x] Cross-module client integration *(Batch 114 — IPD Management workspace wired end-to-end into the desktop client: nav button, RBAC vocabulary + permissions, `ipd_management.js` bed census/admissions/discharge module with HTML-escaped rendering, eight matching `api.js` fetchers; Pharmacy authenticated-user context fixed; 13-test three-layer QA suite incl. `node --check` syntax gates and executed RBAC semantics)*
- [x] Role-aware UI *(Batch 110 — /auth/me profile contract ↔ client RBAC navigation gate locked end-to-end by a 10-test QA suite; deny-by-default, three-fold denial effect, blanket admin roles)*

## Milestone 4 – Printing 🔄

- [x] Print manifest standard ([docs/PRINT_STANDARDS.md](docs/PRINT_STANDARDS.md))
- [x] Client print renderer and batch printing
- [x] Prescription template final QA *(Batch 113 — automated print-pipeline contract suite locks CSS geometry/chrome-hiding, JS fetcher↔renderer↔button consistency over all 16 envelope routes, HTML-escape XSS guard, cold-DB 200s and paper-parity end-to-end)*
- [ ] Printer hardware QA *(automated readiness locked by Batch 113; physical-paper field checklist on target hardware remains an operational task)*
- [x] PDF generation verification *(Batch 117 — verified: server-side deterministic PDF engine `backend/app/services/report_pdf.py` (ReportLab) renders all 16 print-envelope types registered under `/api/v1/reports/*`; unknown/malformed payloads fail loudly; suite green with `reportlab` now pinned in `requirements.txt`.)*

## Milestone 5 – Reports ✅

- [x] Statistics engine and reporting foundation ([docs/STATISTICS_ENGINE.md](docs/STATISTICS_ENGINE.md))
- [x] Administrative and statistical report data (Batches 02–05)
- [x] Report scheduling *(Batch 117 — verified: `app/services/report_scheduler.py` + admin API `/maintenance/report-schedules` (CRUD, hourly due-tick, PDF artifact per fire under `data/scheduled_reports/`, bounded run history, failure isolation); job definitions persisted as `SystemSetting` JSON — no migration needed.)*
- [x] Final reporting/printing integration *(Batch 117 — verified: end-to-end chain envelope JSON → PDF endpoint (`POST /reports/{type}/pdf`) → scheduled fires → client HTML print pipeline (Batches 100–113) all consume the same 16 registered envelope kinds from one registry.)*

## Milestone 6 – Testing ✅

- [x] Unit test suite expansion
- [x] Integration tests across modules
- [x] End-to-end tests
- [x] Multi-client LAN tests (Batch 104 — shared file-backed SQLite/WAL concurrency suite over the full ASGI stack)
- [x] Performance testing
- [x] Clean-machine installation testing (Batch 104 — fresh-directory migration-chain bootstrap, 0001→0028, verified green)

## Milestone 7 – Release 🔶 (in progress — Batches 105–119 landed packaging, EXE build, installer & CI, backup/restore + client launcher, performance & security audit, role-aware UI QA, documentation & training finalization, WebView2 offline redistributable bundling, print pipeline & hardware-readiness QA, cross-module client integration polish, secret-key rotation release gate, docs consolidation, out-of-the-box demo data + default-admin OOBE, tag-driven dual-platform GitHub releases, GUI served by the server itself, Wi-Fi LAN discovery fix, OpenAPI-generation fix and deprecated-utcnow cleanup)

- [x] Client launcher packaging verification (Batch 108 — `client/HHMS.Client` single-file self-contained win-x64 `HHMS-Client.exe` contract locked by QA; WebView2 SDK pinned at 1.0.3856.49; frontend bundled; `-IncludeClient` installer switch; Batch 112 — offline redistributable CAB bundling closed)
- [x] WebView2 runtime packaging *(launcher prerequisite check in `scripts/deploy/server-launch.ps1` done Batch 105; pinned SDK ships in the launcher EXE per Batch 108; Batch 112 — `stage_webview2_redist.ps1` fixed-version CAB staging with SHA-256 pinning + Microsoft-host allow-list, `-Webview2RedistDir` installer bundling via `expand.exe` unpack to `{app}\WebView2Runtime\<version>`, launcher `runtimeDirectory:` consumption; 14-test QA suite)*
- [x] Final server EXE packaging (Batch 106 — real one-file PyInstaller build executed + frozen first-run smoke verified; Batch 107 — Windows EXE automated in CI; Batch 108 — client launcher verification closed)
- [x] Installer & release automation (Batch 107 — `scripts/deploy/build-installer.ps1` Inno Setup/NSIS + `.github/workflows/release.yml` tag-triggered pipeline with SHA-256 checksums and GitHub Release publishing; Batch 108 — `-IncludeClient` launcher bundling)
- [x] Backup / restore workflows (Batch 108 — round-trip, snapshot hygiene, corrupt-upload rejection, admin gating verified on file-backed runtime)
- [x] Performance & security audit pass (Batch 109 — login brute-force rate limiter `app/middleware/rate_limit.py` with structured 429 + `Retry-After` before Argon2 work, settings-tunable budget/window, SQL-level pagination gates, sub-second health probes, JWT audit invariants; 20-test QA suite)
- [x] Role-aware UI & cross-module navigation QA (Batch 110 — `GET /auth/me` profile contract ↔ `frontend/js/rbac.js` navigation gate locked end-to-end: live server-profile-driven visibility, inactive-role filtering, vocabulary completeness, deny-by-default, hidden/disabled/aria-hidden triple; non-numeric-subject 401 product fix; 10-test QA suite)
- [x] Documentation finalization *(Batch 111 — docs/USER_GUIDE.md end-user manual, docs/ADMIN_TRAINING.md administrator handbook, docs/DEVELOPER_ONBOARDING.md contributor guide; all claims grounded in verified repo facts; indexed in docs/INDEX.md with audience reading-order pointers)*
- [x] Deployment scripts (Batch 105 — `scripts/deploy/`: build-server.sh, install-first-run.sh, server-launch.ps1, usage README; syntax/integrity verified by QA suite)
- [x] User training materials *(Batch 111 — USER_GUIDE.md role-driven workflow manual + ADMIN_TRAINING.md hands-on training handbook with day-1 checklist and quarterly restore drill)*
- [x] Secret-key rotation gate *(Batch 115 — runtime secrets untracked + ignored, enforced min-length validation, loader hardening, `rotate-secret-key.ps1` utility, `docs/SECRET_ROTATION_RUNBOOK.md`; executing the rotation per deployment before v1.0 remains an operational step)*
- [x] Automatic dual-platform GitHub releases *(Batch 116 — `release.yml` builds + smoke-tests Linux server bundle and Windows EXE/installer in parallel, computes SHA-256 checksums, publishes a GitHub Release automatically; `--smoke-test` first-run probe added to `server.py`; historical docs consolidated under `docs/history/`. Policy refined in Batches 118–119 and re-closed after Run #D: tag-driven — every push to `main` publishes ONE rolling `nightly` prerelease (stable URL, never accumulates), a `vX.Y.Z` tag publishes the stable "latest" Release; per-commit snapshot releases banned; combined `latest-build` artifact always downloadable from the Actions run page)*
- [x] Out-of-the-box experience (OOBE) *(Batches 117–119 + Runs #H/#I/#F — fresh install is immediately usable with zero commands: migrations → default admin (`admin`/`admin`, opt-out `HHMS_BOOTSTRAP_DEFAULT_ADMIN=false`) → 2025 demo dataset auto-seed on pristine DB only (`HHMS_SEED_DEMO_DATA=false` to disable); web GUI served by the server itself at `/`; LAN discovery port aligned with the C# client probe (38541) with per-subnet Wi-Fi broadcast; `--smoke-test` now exercises the full first-run path so broken OOBE fails CI; OpenAPI/Swagger generation regression guard added; deprecated `datetime.utcnow()` fully removed from `backend/app`)*
- [x] Desktop UX: hidden server console + tray log window + autosave drafts *(packaged Windows server runs with no cmd.exe window; a small live-log window tails the server log and minimises to a system-tray icon on close, with right-click "Exit Server" for proper shutdown; rolling SQLite draft backup saved automatically on every clean exit; frontend autosaves entered data on every step (localStorage drafts restored on reload) — `backend/app/desktop_console.py`, `frontend/js/autosave.js`, tests in `backend/tests/test_desktop_console.py`)*
- [ ] Production release *(execute the Batch 115 rotation runbook on the deployment environment, bump `VERSION`, then push a `v*.*.*` tag — the pipeline publishes both platform artifacts as a stable GitHub Release automatically)*

---

## Current Position

Functional build complete (Milestones 0–6 ✅). Milestone 7 is nearly done: packaging, installers, CI releases, backup/restore, security & performance hardening, role-aware UI, training docs, print-pipeline QA, cross-module integration, secret-rotation gate, automatic dual-platform GitHub releases, and the zero-command out-of-the-box experience (default admin + 2025 demo data + server-served GUI) have all landed and are verified by the full backend suite (**566 passed, 2 skipped**). Demo dataset seeding ships as an OOBE convenience (auto on first run; manual: `python -m app.server seed-demo-data`; see [docs/DEMO_DATA.md](docs/DEMO_DATA.md)).

Remaining before v1.0 (both operational, non-code):
- Printer hardware field checklist on target clinic hardware.
- Execute the [secret rotation runbook](docs/SECRET_ROTATION_RUNBOOK.md) per deployment, bump `VERSION` to 1.0.0, push a `v1.0.0` tag — the release pipeline publishes both platform artifacts as a stable GitHub Release automatically.

Per-batch history lives in [CHANGELOG.md](CHANGELOG.md), [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md) and [docs/history/](docs/history/).
