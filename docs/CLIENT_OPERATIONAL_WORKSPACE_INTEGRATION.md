# Client Operational Workspace Integration

This batch wires the existing Inventory, Procurement, Audit/Service Activity, and Pharmacy client modules into the main HHMS shell.

It also completes the missing procurement API exports used by `procurement.js`.

## Navigation

Global navigation now exposes:
- Inventory
- Procurement
- Audit / Activity

The patient record navigation exposes Pharmacy.

## Authorization

Navigation visibility is driven by the existing client RBAC layer. Server-side authorization remains authoritative.
