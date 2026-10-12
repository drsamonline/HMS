<div align="center">

# 🏥 HHMS — Homeopathic Hospital Management System

**A LAN-based hospital management system purpose-built for homeopathic hospitals and clinics.**

Runs entirely on the local network with a server-owned database — *no internet dependency, no cloud lock-in.*

[![Release policy](https://img.shields.io/badge/releases-nightly%20%2B%20stable-blueviolet)](CHANGELOG.md)
[![Version](https://img.shields.io/badge/version-0.0.1-informational)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-557%20passed-brightgreen)](backend/tests)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue?logo=githubactions&logoColor=white)](.github/workflows/release.yml)
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

## ✨ Features

**Clinical** — patient registration & search, OPD queue with token system, homoeopathic case records, diagnosis/ICD-11, prescriptions, IPD admission with ward/bed management, investigations/laboratory/X-Ray, annual case rollover and archival.

**Operational** — billing & payments with live-derived invoice balances, pharmacy stock ledger with dispense integrity, procurement/goods receipt, department/service/designation masters, role-based dashboards (outstanding billing, bed occupancy, pending investigations, OPD queue, discharge audit).

**Reporting & printing** — statistics engine, 16 screen/paper-parity print envelopes (receivables aging, collection summaries, receipt continuity, settlement/refund audits, ward occupancy, investigation billing reconciliation), PDF generation, report scheduling, batch printing.

**Release-ready infrastructure** — LAN server discovery (UDP port 38541), single-file Windows/Linux server binaries, Inno/NSIS installers, automatic dual-platform GitHub releases (rolling `nightly` prerelease on every push to `main`, stable Release on `v*.*.*` tags), backup/restore workflows, login rate limiting, JWT hardening, secret-key rotation runbook. **557 backend tests passing.**

---

## 🚀 Quick Start

```bash
cd backend
pip install -r requirements.txt
python -m app.server
```

The server runs migrations automatically, creates the default administrator
(`admin` / `admin` — change it immediately; disable with
`HHMS_BOOTSTRAP_DEFAULT_ADMIN=false`), seeds a full **2025 demo dataset**
on first run (no commands needed — see below), serves the built-in web GUI at
`http://localhost:8000/`, and listens on the configured LAN port. See
[SERVER_STARTUP](docs/SERVER_STARTUP.md) and
[DEPLOYMENT_ARCHITECTURE](docs/DEPLOYMENT_ARCHITECTURE.md) for production setup.

### Demo data (automatic on first run — no commands)

On a brand-new install the server seeds a full year of realistic demo data by
itself at startup — patients, OPD tokens, cases, prescriptions, dispenses, lab
results, admissions, invoices and payments — so the GUI is populated the
moment you open it. Portable builds (folder or EXE) work out of the box:
copy → run → log in as `admin` / `admin`.

- The seed runs **only** when the database is pristine; any install that
  already contains real data is never touched.
- Opt out with environment variable `HHMS_SEED_DEMO_DATA=false` (recommended
  for production deployments).
- Optional manual commands (not required): `python -m app.server
  seed-demo-data` supports `--year` and `--force`. Details:
  [docs/DEMO_DATA.md](docs/DEMO_DATA.md).

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
