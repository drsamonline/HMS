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
- ✔ IPD admission and clinical documentation
- ✔ Investigations / laboratory / X-Ray

### ⚙️ Operational
- ✔ Billing and payments
- ✔ Dashboard outstanding-billing receivables feed *(Batch 82)*
- ✔ Dashboard IPD bed-occupancy continuity feed *(Batch 83)*
- ✔ Dashboard laboratory pending-investigation backlog feed *(Batch 84)*
- ✔ MRD / patient files / archives
- ✔ Department and service masters
- ✔ Clinical activity and statistics

### 🖨️ Reporting & Printing
- ✔ Reporting and print manifests
- ✔ Client-side report rendering and batch printing
- ✔ Invoice print envelope with live payment-derived balances *(Batch 85)*
- ✔ Receivables aging ledger — `GET /dashboard/receivables-aging` with
  standard 0–30 / 31–60 / 61–90 / Over-90 buckets over the Batch 82
  outstanding-invoice (live-payment) derivation, printable aging preview in
  the Reports & Printing workspace *(Batch 86)*
- ✔ Invoice receipt continuity report — `GET /dashboard/invoice-receipt-continuity`
  audits receipt-book integrity over live payments (missing receipts,
  duplicate receipt numbers, numeric sequence breaks), printable continuity
  audit with headline aggregates in the Reports & Printing workspace *(Batch 87)*
- ✔ Receipt numbering continuity audit — `GET /dashboard/receipt-numbering-continuity`
  reconciles the whole receipt book by numeric series (missing numbers,
  duplicates, `expected == actual + gaps` invariant), printable numbering
  audit in the Reports & Printing workspace *(Batch 88)*
- ✔ Invoice payment reconciliation ledger — `GET /dashboard/invoice-payment-reconciliation`
  checks every scanned invoice against the live Payment ledger with
  derived-vs-stored status drift detection, printable reconciliation ledger
  in the Reports & Printing workspace *(Batch 89)*
- ✔ Collection summary by patient — `GET /dashboard/collection-summary-by-patient`
  rolls the reconciliation ledger into per-patient billed / collected /
  outstanding totals (`total_collected + outstanding == total_billed`), with a
  printable collection summary envelope sharing the same scan/aggregation and
  a Reports & Printing workspace card *(Batch 90)*
- ✔ Receivables aging print envelope — `POST /reports/receivables-aging-print-envelope`
  builds the printable aging packet through the exact shared derivation
  (`build_receivables_aging_result`) behind `GET /dashboard/receivables-aging`,
  so printed buckets always reconcile line-for-line with the screen; the
  Reports & Printing aging card now prepares through the envelope *(Batch 91)*
- ✔ Invoice receipt continuity print envelope — `POST /reports/invoice-receipt-continuity-print-envelope`
  builds the printable continuity audit through the exact shared scan +
  derivation (`_load_continuity_scan_inputs` / `build_invoice_receipt_continuity_result`)
  behind `GET /dashboard/invoice-receipt-continuity`, so printed headline
  aggregates always sum back to `invoices_checked` and match the screen; the
  Reports & Printing continuity card now prepares through the envelope *(Batch 92)*
- ✔ Receipt numbering continuity print envelope — `POST /reports/receipt-numbering-continuity-print-envelope`
  builds the printable numbering audit through the exact shared whole-book
  derivation (`build_receipt_numbering_continuity_result`) behind
  `GET /dashboard/receipt-numbering-continuity`, so printed series lines and
  headline aggregates (`expected == actual + gaps`) always match the screen;
  the Reports & Printing numbering card now prepares through the envelope *(Batch 93)*

### 🧪 Test Suite
- 289 backend tests passing as of Batch 93 (see [CHANGELOG.md](CHANGELOG.md)).

### 🌐 Infrastructure
- ✔ LAN discovery and client/server connection
- ✔ Annual case rollover and archival lifecycle *(Batch 69)*

---

## 🚧 Remaining Release Work

- ⬜ Cross-module client integration
- ⬜ Role-aware UI
- ⬜ Final print/printer QA
- ⬜ WebView2 runtime packaging
- ⬜ Multi-client LAN tests
- ⬜ Backup/restore and recovery
- ⬜ Performance/security audit
- ⬜ Final EXE packaging and clean-machine installation

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
