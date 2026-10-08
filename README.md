<div align="center">

# 🏥 HHMS — Homeopathic Hospital Management System

**A LAN-based hospital management system purpose-built for homeopathic hospitals and clinics.**

Runs entirely on the local network with a server-owned database — *no internet dependency, no cloud lock-in.*

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/drsamonline/hhms?label=release&color=blue)](CHANGELOG.md)
[![Version](https://img.shields.io/badge/version-0.0.1-informational)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue?logo=python&logoColor=white)](backend/pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/database-SQLite%20%2B%20Alembic-003b57?logo=sqlite&logoColor=white)](docs/DATABASE_SCHEMA.md)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20LAN-lightgrey)](docs/DEPLOYMENT_ARCHITECTURE.md)
[![Docs](https://img.shields.io/badge/docs-INDEX-green)](docs/INDEX.md)

</div>

---

## 📐 Architecture at a Glance

```text
┌──────────────────┐        ┌──────────────────┐        ┌─────────────────────────┐
│  HHMS-Client.exe │ ─────► │   LAN HTTP/JSON  │ ─────► │  HHMS-Server.exe        │
│  (WebView2 UI)   │        │                  │        │  (server-owned SQLite)  │
└──────────────────┘        └──────────────────┘        └─────────────────────────┘
```

| Layer | Description |
|-------|-------------|
| 💻 **Client** | Lightweight HTML/CSS/vanilla-JavaScript interface hosted in WebView2 |
| 🔌 **Transport** | HTTP/JSON over the hospital LAN with automatic server discovery |
| 🗄️ **Server** | The only component that touches the shared SQLite database — the client never opens it directly |

📖 Details: [DEPLOYMENT_ARCHITECTURE](docs/DEPLOYMENT_ARCHITECTURE.md) · [BACKEND_ARCHITECTURE](docs/BACKEND_ARCHITECTURE.md) · [FRONTEND_ARCHITECTURE](docs/FRONTEND_ARCHITECTURE.md)

---

## 📁 Repository Layout

| Path | Contents |
|------|----------|
| [`backend/`](backend) | Python server: API routers, services, models, Alembic migrations, tests |
| [`frontend/`](frontend) | Client UI: HTML, CSS, and vanilla JavaScript modules |
| [`client/`](client) | Native Windows client host (WebView2 shell) |
| [`docs/`](docs) | Full specification, architecture, workflow, and batch documentation ([index](docs/INDEX.md)) |
| [`.ai/`](.ai) | Project constitution, coding rules, decisions, and state tracking |
| [`data/`](data) | Runtime data directory (server-owned database and secrets) |

---

## ✅ Implemented Areas

### 🩺 Clinical
- ✔ Patient registration and search
- ✔ OPD / visits / OPD tokens
- ✔ Homoeopathic case records
- ✔ Diagnosis and ICD-11
- ✔ Prescriptions and medicines
- ✔ IPD admission, ward/bed management and clinical documentation
- ✔ Investigations / laboratory / X-Ray
- ✔ Annual case rollover and archival lifecycle *(Batch 69)*

### ⚙️ Operational
- ✔ Billing and payments (live-payment-derived invoice balances)
- ✔ Dashboard feeds — outstanding billing, IPD bed-occupancy continuity,
  laboratory pending-investigation backlog *(Batches 82–84)*
- ✔ MRD / patient files / archives
- ✔ Department and service masters
- ✔ Clinical activity and statistics

### 🖨️ Reporting & Printing
- ✔ Reporting and print manifests, client-side report rendering, batch printing
- ✔ A family of **screen/paper-parity audit surfaces** (Batches 85–102): each
  dashboard feed is derived by one shared scan/service and mirrored by a
  matching print envelope (`POST /reports/...-print-envelope`), so printed
  figures reconcile line-for-line with the screen by construction:
  - Receivables aging ledger + print envelope *(Batches 86, 91)*
  - Invoice receipt continuity & receipt numbering continuity (+ envelopes) *(Batches 87–88, 92–93)*
  - Invoice payment reconciliation ledger & collection summary by patient (+ envelopes) *(Batches 89–90, 94–95)*
  - Payment-method collection summary & overpayment breakdown *(Batches 96, 98)*
  - Invoice overpayment ledger *(Batch 97)* · Invoice settlement audit & refund audit *(Batch 100)*
  - Discharge audit & OPD queue daily summary (+ operational envelopes) *(Batches 99–100)*
  - Ward occupancy summary + print envelope *(Batch 101)*
  - Investigation billing reconciliation + print envelope *(Batch 102)*
- ✔ Reports & Printing workspace cards for every surface above *(Batch 100 ghost-card fix)*

### 🧪 Quality Assurance (Milestone 6 — complete)
- ✔ Full-stack E2E route suite + cross-module integration + performance smoke
  benchmark; fixed a release-blocking login 500 (`hashed_password` vs
  `password_hash` column mismatch) *(Batch 103)*
- ✔ Multi-client LAN concurrency suite on a shared file-backed WAL SQLite DB
  (parallel logins / registrations / token mints, UDP `HHMS_DISCOVER_V1`
  discovery handshake) and clean-machine installation simulation (fresh-dir
  Alembic bootstrap 0001→0028, ORM/schema parity, empty-DB auth round-trip);
  fixed three release-blocking defects: StaticPool concurrency deadlock,
  migration-chain gaps incl. missing base tables in 0018, and 184 missing
  `CURRENT_TIMESTAMP` server defaults *(Batch 104)*
- ✔ **546 backend tests passing** as of Batch 116 — see [CHANGELOG.md](CHANGELOG.md)

### 📦 Release Engineering (Milestone 7 — in progress)
- ✔ Single-source versioning from the root `VERSION` file, resolved across
  source / packaged / PyInstaller-frozen layouts and surfaced by `/health`
  (`backend/app/release_version.py`) *(Batch 105)*
- ✔ Frozen-runtime Alembic execution via a bundled PyInstaller hook +
  updated `HHMS-Server.spec` *(Batch 105)*
- ✔ Deployment scripts in `scripts/deploy/` (`build-server.sh`,
  `install-first-run.sh`, Windows `server-launch.ps1` with WebView2
  prerequisite check), validated by an 18-test packaging QA suite *(Batch 105)*
- ✔ Real one-file EXE build executed end-to-end + frozen first-run smoke
  (migrations to head, `/health` version handshake, structured 401); five
  build/runtime defects fixed incl. lazy-DBAPI hidden imports *(Batch 106)*
- ✔ Windows installer builder `scripts/deploy/build-installer.ps1` (Inno Setup
  with NSIS fallback; user-writable install dir; patient data preserved on
  uninstall) and CI release pipeline `.github/workflows/release.yml`
  (test-gated Linux bundle + Windows EXE/installer builds + SHA-256
  checksummed GitHub Releases), gated by a 10-test QA suite *(Batch 107)*
- ✔ Backup/restore & recovery workflows verified end-to-end on the packaged
  file-backed runtime (point-in-time restore, snapshot hygiene, corrupt-upload
  rejection, byte-exact downloads, admin gating) *(Batch 108)*
- ✔ Client launcher packaging contract (`HHMS-Client.exe`): single-file
  self-contained win-x64 publish, WebView2 SDK pinned at 1.0.3856.49, frontend
  bundled, LAN discovery bridge, version lock-step with `VERSION`; installer
  `-IncludeClient` switch bundles it into Inno/NSIS setups; 11-test QA suite
  *(Batch 108)*
- ✔ Performance & security audit pass: dependency-free sliding-window login
  rate limiter (`app/middleware/rate_limit.py`, structured 429 + `Retry-After`
  before Argon2 work, env-tunable budget/window), SQL-level pagination bounds,
  sub-second health-probe gate, JWT audit invariants (reserved claims,
  expiry/tamper rejection, HS256 pinning, secret entropy); 20-test QA suite
  *(Batch 109)*
- ✔ Role-aware UI & cross-module navigation QA: `GET /auth/me` profile contract locked end-to-end against the client RBAC
  gate (`frontend/js/rbac.js`) — live server-profile-driven visibility, inactive-role filtering, vocabulary completeness,
  deny-by-default, hidden/disabled/aria-hidden triple; non-numeric-subject JWT crash fixed to structured 401;
  10-test QA suite *(Batch 110)*
- ✔ Documentation & training finalization: three audience guides — `docs/USER_GUIDE.md` (end-user workflow
  manual), `docs/ADMIN_TRAINING.md` (administrator handbook with day-1 checklist + restore drill),
  `docs/DEVELOPER_ONBOARDING.md` (contributor onboarding) — all claims grounded in verified repo facts;
  indexed with audience reading-order pointers *(Batch 111)*
- ✔ WebView2 offline redistributable bundling for air-gapped installs: `stage_webview2_redist.ps1`
  fixed-version CAB staging (HTTPS + Microsoft-host allow-list, SHA-256 pinning, `redist-manifest.json`),
  installer `-Webview2RedistDir` switch with checksum re-verification and `expand.exe` unpack into
  `{app}\WebView2Runtime\<version>` (Inno + NSIS), launcher `runtimeDirectory:` consumption with
  Evergreen fallback; 14-test QA suite *(Batch 112)*
- ✔ Print pipeline & hardware-readiness QA: three-layer contract suite (print.css geometry/chrome-hiding,
  JS fetcher↔renderer↔button consistency over all 16 envelope routes + HTML-escape XSS guard, cold-DB 200s,
  paper-parity end-to-end invoice packet); refund-audit cold-DB crash fixed in `reporting.py`; 11-test suite
  *(Batch 113)*
- ✔ Cross-module client integration polish: IPD Management workspace wired end-to-end into the desktop client
  (nav button, RBAC vocabulary + permissions, `ipd_management.js` bed census/admissions/discharge module with
  HTML-escaped rendering, eight matching `api.js` fetchers); Pharmacy authenticated-user context fixed;
  13-test three-layer QA suite incl. `node --check` syntax gates and executed RBAC semantics *(Batch 114)*
- ✔ Repository hygiene: linearized history, secret-hygiene sweep (334 stale
  runtime/cache artifacts untracked), hardened `.gitignore` *(Batches 105–cleanup)*

### 🌐 Infrastructure
- ✔ LAN discovery and client/server connection

---

## 🚧 Remaining Release Work *(Milestone 7)*

- ✅ Final server EXE build *(Batch 106 — one-file Linux artifact built & smoke-tested; Windows EXE + installer automated in CI, Batch 107)*
- ✅ Installer & release automation *(Batch 107 — build-installer.ps1 + release.yml tag-triggered pipeline with checksums)*
- ✅ Client launcher packaging verification — `HHMS-Client.exe` single-file self-contained publish contract locked by QA, WebView2 SDK pinned, installer `-IncludeClient` bundling *(Batch 108; offline redistributable CAB bundling closed Batch 112)*
- ✅ Backup / restore and recovery workflows *(Batch 108 — round-trip, snapshot hygiene, corrupt-upload rejection, admin gating verified on file-backed runtime)*
- ✅ Performance & security audit pass *(Batch 109 — login brute-force rate limiter with 429 + Retry-After, pagination/health performance gates, JWT audit invariants)*
- ✅ Role-aware UI & cross-module navigation QA *(Batch 110 — /auth/me profile contract ↔ client RBAC gate locked by a 10-test suite; non-numeric-subject 401 fix)*
- ✅ Documentation & training finalization *(Batch 111 — user/admin/developer audience guides, docs/INDEX.md reading-order pointers)*
- ✅ WebView2 offline redistributable bundling *(Batch 112 — `stage_webview2_redist.ps1` CAB staging with SHA-256 pinning + host allow-list, installer `-Webview2RedistDir` unpack to `{app}\WebView2Runtime`, launcher `runtimeDirectory:` consumption; 14-test QA suite)*
- ✅ Print pipeline & hardware-readiness QA *(Batch 113 — three-layer contract suite: CSS/JS/backend, cold-DB 200s, paper-parity E2E; refund-audit cold-DB crash fixed; physical-paper field checklist on target hardware remains an operational task)*
- ✅ Cross-module client integration polish *(Batch 114 — IPD Management workspace wired end-to-end into the desktop client: nav button + RBAC vocabulary + `ipd_management.js` bed census/admissions/discharge module with HTML-escaped rendering + eight matching `api.js` fetchers; Pharmacy user-context fix; 13-test three-layer QA suite incl. `node --check` syntax gates and executed RBAC semantics)*
- ✅ Automatic dual-platform GitHub releases *(Batch 116 — `release.yml` rewritten: on `v*` tags the pipeline runs the regression gate, then builds + smoke-tests the Linux one-file server bundle and the Windows EXE + installer in parallel jobs, computes SHA-256 checksums, and publishes everything to a GitHub Release automatically; new `--smoke-test` first-run probe in `backend/app/server.py`; docs clutter consolidated into `docs/history/`; 15-test QA suite)*
- ✅ Secret-key rotation & production release gate *(Batch 115 — runtime secrets untracked/ignored, enforced `min_length` validation + loader hardening, `rotate-secret-key.ps1` utility, `docs/SECRET_ROTATION_RUNBOOK.md`; per-deployment rotation before v1.0 remains an operational step)*
- ✅ Multi-client LAN tests *(Batch 104 — WAL SQLite concurrency + UDP discovery handshake)*
- ✅ Clean-machine database installation *(Batch 104 — fresh-dir Alembic bootstrap 0001→0028)*

> 📊 Progress is tracked per batch in [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md) and planned in [ROADMAP.md](ROADMAP.md).

---

## 🔧 Development Workflow

1. Use the latest verified repository ZIP as the source of truth.
2. Implement work in coherent batches (largest safe batch).
3. Verify each batch against the intended change set.
4. Stage exact files and commit/push only after the staged audit is green.

📜 Full rules: [CONTRIBUTING.md](CONTRIBUTING.md) · [IMPLEMENTATION_RULES](docs/IMPLEMENTATION_RULES.md) · [CODING_RULES](.ai/CODING_RULES.md)

---

## 🗺️ Documentation Map

| Area | Start Here |
|------|------------|
| 📇 Master index | [docs/INDEX.md](docs/INDEX.md) |
| 📋 Functional scope | [docs/MASTER_SPECIFICATION.md](docs/MASTER_SPECIFICATION.md) |
| 🗃️ Database | [DATABASE_ENTITIES](docs/DATABASE_ENTITIES.md) · [DATABASE_SCHEMA](docs/DATABASE_SCHEMA.md) |
| 🔗 API | [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md) |
| 🔐 Security | [SECURITY_ARCHITECTURE](docs/SECURITY_ARCHITECTURE.md) · [SECURITY.md](SECURITY.md) |
| 🎨 UI & printing | [UI_GUIDELINES](docs/UI_GUIDELINES.md) · [PRINT_STANDARDS](docs/PRINT_STANDARDS.md) |
| 🧪 Testing | [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) |
| 🚀 Deployment & releases | [docs/DEPLOYMENT_ARCHITECTURE.md](docs/DEPLOYMENT_ARCHITECTURE.md) · [CHANGELOG.md](CHANGELOG.md) |
| 📖 Terminology | [docs/GLOSSARY.md](docs/GLOSSARY.md) |

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and follow the project rules in [.ai/CODING_RULES.md](.ai/CODING_RULES.md) before opening a pull request. Found a security issue? See [SECURITY.md](SECURITY.md).

---

## 📄 License

Released under the [MIT License](LICENSE). See [CHANGELOG.md](CHANGELOG.md) for release history.

<div align="center">

Made with ❤️ for homeopathic hospitals — **HHMS Project © 2025**

</div>
