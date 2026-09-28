# 🏥 HHMS — Homeopathic Hospital Management System

HHMS is a **LAN-based hospital management system** purpose-built for homeopathic hospitals and clinics. It runs entirely on the local network with a server-owned database — no internet dependency, no cloud lock-in.

---

## Architecture at a Glance

```text
┌──────────────────┐        ┌──────────────────┐        ┌─────────────────────────┐
│  HHMS-Client.exe │ ─────► │   LAN HTTP/JSON  │ ─────► │  HHMS-Server.exe        │
│  (WebView2 UI)   │        │                  │        │  (server-owned SQLite)  │
└──────────────────┘        └──────────────────┘        └─────────────────────────┘
```

- **Client** — lightweight HTML/CSS/vanilla-JavaScript interface hosted in WebView2.
- **Transport** — HTTP/JSON over the hospital LAN with automatic server discovery.
- **Server** — the only component that touches the shared SQLite database; the client never opens it directly.

See [docs/DEPLOYMENT_ARCHITECTURE.md](docs/DEPLOYMENT_ARCHITECTURE.md), [docs/BACKEND_ARCHITECTURE.md](docs/BACKEND_ARCHITECTURE.md) and [docs/FRONTEND_ARCHITECTURE.md](docs/FRONTEND_ARCHITECTURE.md) for details.

---

## Repository Layout

| Path | Contents |
|------|----------|
| [`backend/`](backend) | Python server: API routers, services, models, Alembic migrations, tests |
| [`frontend/`](frontend) | Client UI: HTML, CSS, and vanilla JavaScript modules |
| [`client/`](client) | Native Windows client host (WebView2 shell) |
| [`docs/`](docs) | Full specification, architecture, workflow, and batch documentation ([index](docs/INDEX.md)) |
| [`.ai/`](.ai) | Project constitution, coding rules, decisions, and state tracking |
| [`data/`](data) | Runtime data directory (server-owned database and secrets) |

---

## Implemented Areas

### Clinical
- ✅ Patient registration and search
- ✅ OPD / visits / OPD tokens
- ✅ Homoeopathic case records
- ✅ Diagnosis and ICD-11
- ✅ Prescriptions and medicines
- ✅ IPD admission and clinical documentation
- ✅ Investigations / laboratory / X-Ray

### Operational
- ✅ Billing and payments
- ✅ MRD / patient files / archives
- ✅ Department and service masters
- ✅ Clinical activity and statistics

### Reporting & Printing
- ✅ Reporting and print manifests
- ✅ Client-side report rendering and batch printing

### Infrastructure
- ✅ LAN discovery and client/server connection
- ✅ Annual case rollover and archival lifecycle (Batch 69)

---

## Remaining Release Work

- ⬜ Cross-module client integration
- ⬜ Role-aware UI
- ⬜ Final print/printer QA
- ⬜ WebView2 runtime packaging
- ⬜ Multi-client LAN tests
- ⬜ Backup/restore and recovery
- ⬜ Performance/security audit
- ⬜ Final EXE packaging and clean-machine installation

Progress is tracked per batch in [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md) and planned in [ROADMAP.md](ROADMAP.md).

---

## Development Workflow

1. Use the latest verified repository ZIP as the source of truth.
2. Implement work in coherent batches (largest safe batch).
3. Verify each batch against the intended change set.
4. Stage exact files and commit/push only after the staged audit is green.

Full rules: [CONTRIBUTING.md](CONTRIBUTING.md) · [docs/IMPLEMENTATION_RULES.md](docs/IMPLEMENTATION_RULES.md) · [.ai/CODING_RULES.md](.ai/CODING_RULES.md)

---

## Documentation Map

| Area | Start Here |
|------|------------|
| Master index | [docs/INDEX.md](docs/INDEX.md) |
| Functional scope | [docs/MASTER_SPECIFICATION.md](docs/MASTER_SPECIFICATION.md) |
| Database | [docs/DATABASE_ENTITIES.md](docs/DATABASE_ENTITIES.md) · [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) |
| API | [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md) |
| Security | [docs/SECURITY_ARCHITECTURE.md](docs/SECURITY_ARCHITECTURE.md) · [SECURITY.md](SECURITY.md) |
| UI & printing | [docs/UI_GUIDELINES.md](docs/UI_GUIDELINES.md) · [docs/PRINT_STANDARDS.md](docs/PRINT_STANDARDS.md) |
| Testing | [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) |
| Terminology | [docs/GLOSSARY.md](docs/GLOSSARY.md) |

---

## License

Released under the [MIT License](LICENSE). See [CHANGELOG.md](CHANGELOG.md) for release history.
