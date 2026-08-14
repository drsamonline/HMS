# Client Clinical Context Integration — Batch 28

The client now maintains a lightweight session-scoped clinical context containing the current patient, selected visit, case record and, when applicable, admission.

The context is consumed by downstream workflows that require an encounter:

- Investigations send `visit_id` or `admission_id` to the existing backend API.
- Billing invoices send the current `visit_id` or `admission_id` when available.

This prevents creation of orphan investigations and invoices and avoids asking users to manually re-enter encounter identifiers.

The context is stored only in `sessionStorage`. It is UI/session state, not a clinical database record. The backend remains authoritative and validates patient/encounter ownership.
