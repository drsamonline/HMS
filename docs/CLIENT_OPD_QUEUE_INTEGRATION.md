# Client OPD Queue Integration

Batch 49 integrates the existing OPD queue workspace into the global HHMS client navigation and RBAC layer.

## Scope
- OPD Queue global navigation entry.
- RBAC access mapping for OPD.
- Existing OPD visit/token workspace reused without duplicating business logic.
- Server remains authoritative for visit and token generation/state.

## Out of scope
- No new OPD database model.
- No token generation in the client.
- No comprehensive QA; that follows functional completion.
