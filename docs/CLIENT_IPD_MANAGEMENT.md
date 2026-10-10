# Client IPD Management

## Scope
Functional client workspace for IPD bed census and active admissions.

## Features
- Filter beds by ward and occupancy status.
- Create bed records through the existing bed API.
- View active admissions.
- Admit a patient into an available bed.
- Use authenticated user identity for `admitted_by`.

The backend remains authoritative for bed occupancy and admission validation.
