# Client Audit & Activity Trail — Batch 45

Adds a read-only activity workspace that combines the existing departmental `ServiceActivity` ledger with a server-side `AuditLog` query.

The audit endpoint is read-only; authorization remains server-side. No new audit table is introduced because `AuditLog` already exists in the database model.

The service-activity view supports an optional patient filter for use inside the patient workspace.
