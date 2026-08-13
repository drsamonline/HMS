# HHMS — Homeopathic Hospital Management System

HHMS is a LAN-based hospital management system designed for homeopathic hospitals and clinics.

## Current architecture

```text
HHMS-Client.exe
    ↓
LAN HTTP/JSON
    ↓
HHMS-Server.exe
    ↓
server-owned SQLite database
```

The client uses a lightweight HTML/CSS/vanilla-JavaScript interface hosted in WebView2. The client never opens the shared SQLite database directly.

## Implemented areas

- Patient registration and search
- OPD / visits / OPD tokens
- Homoeopathic case records
- Diagnosis and ICD-11
- Prescriptions and medicines
- IPD admission and clinical documentation
- Investigations / laboratory / X-Ray
- Billing and payments
- MRD / patient files / archives
- Department and service masters
- Clinical activity and statistics
- Reporting and print manifests
- Client-side report rendering and batch printing
- LAN discovery and client/server connection

## Remaining release work

- Cross-module client integration
- Role-aware UI
- Final print/printer QA
- WebView2 runtime packaging
- Multi-client LAN tests
- Backup/restore and recovery
- Performance/security audit
- Final EXE packaging and clean-machine installation

## Development workflow

Use the latest verified repository ZIP as the source of truth, implement in coherent batches, verify each batch, stage exact files, and commit/push only after the staged audit is green.
