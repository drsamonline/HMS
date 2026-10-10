# Client RBAC Navigation

The client now consumes `GET /api/v1/auth/me` and uses returned roles/permission codes to control top-level navigation visibility.

This is a presentation-layer gate only. Server-side API authorization remains authoritative.

Administrator roles (`admin`, `administrator`, `hospital administrator`, `super administrator`) receive all top-level modules. Other users are evaluated against module-specific permission code aliases. When no permission codes have yet been assigned, the navigation remains visible so existing installations do not lock users out; the backend still enforces authorization.

Modules: Patients, Statistics, Reports/Printing.
