# Batch 62 — API Router Convergence

The project contains a broad set of functional backend modules, but the API root registration had become fragmented: some routers were omitted, some were referenced before import, and newer workflow endpoints were appended after the module's public export block.

Batch 62 consolidates router imports and registration in one place without changing the business logic of those modules.

## Registered workflow groups
- Core/session
- Clinical/pharmacy
- IPD
- Laboratory and assessments
- Billing
- Medical records/history
- Administration/reporting/system operations

The purpose is to make the implemented backend modules reachable through the authoritative API router before further cross-module feature work and later QA.
