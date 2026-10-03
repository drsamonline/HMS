# Client Clinical Workflow Integration

## Scope

This batch makes Visit the shared encounter context for the clinical workspace.

The client can create/select a patient Visit and uses that visit ID when creating a Case Record, Diagnosis, Prescription, and Follow-up. Prescription history is loaded by Visit.

## Empty-data behavior

No existing visit creates a clean New Visit state. A new Case Record can still be drafted after a visit is saved. Optional clinical fields remain independently nullable.

## Security

The current authenticated user is read from `/auth/me` for doctor attribution. The server remains authoritative for authorization and validation.
