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
- ✔ Investigation billing reconciliation — dashboard proof feed + print envelope
  (`GET /dashboard/investigation-billing-reconciliation`, `POST
  /reports/investigation-billing-reconciliation-print-envelope`) sharing one scan/
  derivation trio for screen/paper parity, closing the lab/billing boundary
  *(Batch 102)*
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
- ✔ Invoice payment reconciliation print envelope — `POST /reports/invoice-payment-reconciliation-print-envelope`
  builds the printable reconciliation packet through the exact shared live-scan
  derivation (`build_invoice_payment_reconciliation_ledger`) behind
  `GET /dashboard/invoice-payment-reconciliation`, so printed headlines always
  satisfy `paid + partial + unpaid == invoices_checked` and
  `total_billed == total_paid + total_outstanding`; the Reports & Printing
  reconciliation card now prepares through the envelope *(Batch 94)*
- ✔ Collection summary print envelope — `POST /reports/collection-summary-print-envelope`
  builds the printable per-patient collection packet through the exact shared
  scan/aggregation (`_build_reconciliation_rows` + `build_collection_summary_by_patient`)
  behind `GET /dashboard/collection-summary-by-patient`, so printed headlines always
  satisfy `total_billed == total_collected + total_outstanding`; the Reports & Printing
  collection summary card now prepares through the envelope *(Batch 95)*
- ✔ Payment method collection summary — `GET /dashboard/payment-method-summary` +
  `POST /reports/payment-method-summary-print-envelope` roll the live payment scan
  into per-method receipt counts, gross received vs collected (Batch 68 clamp
  parity) and percentage shares (`sum(per-method collected) == total_collected`),
  through one shared derivation (`build_payment_method_summary_result`) behind both
  surfaces; a Reports & Printing workspace card prepares through the envelope *(Batch 96)*
- ✔ Invoice overpayment ledger — `GET /dashboard/invoice-overpayments` surfaces
  what the Batch 68/89 clamp conceals: invoices whose live un-clamped payment
  total exceeds the billed amount, with `overpaid_amount == total_paid_raw -
  total_amount` per row and `total_paid_raw == total_billed + total_overpaid`
  headlines, derived by the shared `build_overpayment_ledger` /
  `build_overpayment_ledger_result` pair; printable through
  `POST /reports/invoice-overpayment-print-envelope` *(Batch 97)*
- ✔ Payment method overpayment breakdown — `GET /dashboard/payment-method-overpayments` +
  `POST /reports/payment-method-overpayment-print-envelope` split the scan
  window's over-collection across payment methods (per-method gross received,
  collected and overpaid remainder; `total_gross == total_collected +
  total_overpaid`) through the shared `build_payment_method_overpayment_breakdown`
  / `build_payment_method_overpayment_result` pair *(Batch 98)*
- ✔ Discharge audit — `GET /dashboard/discharge-audit` reconciles every recent
  discharge against its admission status and bed occupancy (`admission_discharged`,
  `bed_freed`, `is_reconciled`; `reconciled_count + drift_count == total_discharges`)
  through one shared derivation (`build_discharge_audit_result` /
  `build_discharge_audit_scan`); drifted rows stay visible with actionable cards on
  the dashboard *(Batch 99)*
- ✔ OPD queue daily summary — `GET /dashboard/opd-queue-summary` rolls live OPD
  token rows up per queue day (newest first) with a status split that always sums
  to the day total (`waiting + in_consultation + completed + cancelled ==
  total_tokens`), derived by the shared `build_opd_queue_summary_result` /
  `build_opd_queue_summary_scan` pair behind a single grouped pass *(Batch 99)*
- ✔ Invoice settlement audit — `GET /dashboard/invoice-settlement-audit` rolls the
  live reconciliation scan into per-invoice settled/outstanding lines (Batch 68
  clamp parity; `settled_amount + outstanding_amount == total_amount` per row,
  `cleared_count + unsettled_count == total_invoices`) with refund counts from one
  grouped negative-payment pass; printable through
  `POST /reports/invoice-settlement-audit-print-envelope` *(Batch 100)*
- ✔ Refund audit — `GET /dashboard/refund-audit` scans negative Payment rows
  (newest first) and flags each refund via `invoice_exists` / `has_remarks` /
  `net_non_negative` → `processing_complete`, with
  `processed_count + drifted_count == total_refunds`; printable through
  `POST /reports/refund-audit-print-envelope` *(Batch 100)*
- ✔ Operational print envelopes — discharge audit and OPD queue summary now honor
  the Batch 99 "future print envelope" hooks via
  `POST /reports/discharge-audit-print-envelope` and
  `POST /reports/opd-queue-summary-print-envelope`, reusing the exact shared
  scan/derivation pairs for screen/paper parity by construction *(Batch 100)*
- ✔ Ghost-card fix — the Batch 97 invoice overpayment ledger, server-complete but
  unreachable from the UI, gained an "Invoice overpayment ledger" card plus cards
  for all four new surfaces in the Reports & Printing workspace *(Batch 100)*
- ✔ Ward occupancy summary — `GET /dashboard/ward-occupancy-summary` rolls active beds
  into per-ward buckets (null wards surface under an explicit "Unassigned" label;
  `occupied_beds + reserved_beds + available_beds == total_beds` for any input,
  `active_admissions <= occupied_beds`) via the shared
  `build_ward_occupancy_summary_scan`/`build_ward_occupancy_summary_result` pair;
  printable through `POST /reports/ward-occupancy-print-envelope`, alongside the OPD
  queue summary print preview renderer *(Batch 101)*
- ✔ Investigation billing reconciliation — `GET
  /dashboard/investigation-billing-reconciliation` proves every open lab order
  still carries its billed amount on a live non-cancelled invoice (billed amounts
  re-derived from `InvoiceItem` line totals in one grouped pass, never trusted from
  stored counters; each row keeps `billed_amount == charged_total - credited_total`;
  unbilled orders surface with `billed_amount == 0` instead of disappearing) via the
  shared scan/result trio; printable through `POST
  /reports/investigation-billing-reconciliation-print-envelope` *(Batch 102)*

### 🧪 Test Suite
- 381 backend tests passing as of Batch 102 (see [CHANGELOG.md](CHANGELOG.md)).

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
