# HHMS Validation Rules

## General
- Required identifiers must be present before API submission.
- Optional clinical fields may be empty.
- Empty optional blocks must not prevent saving or retrieval.
- Enumerated values must be validated against their allowed values.
- Date ranges must reject an end value earlier than the start value.
- Numeric quantities must be non-negative unless a domain explicitly permits otherwise.

## Clinical
- Patient context must be known before creating patient-linked records.
- Case records, diagnoses, prescriptions, and follow-ups remain separate records.
- ICD-11 values are optional and may be added when available.
- Modalities support Agg./Amel. plus free-text additional information.
- Narrative sections remain free-text capable.

## Statistics
- Hospital unique-patient totals use distinct patient IDs.
- Activity totals count actual clinical/service activity.
- Department/service unique-patient counts are distinct within their scope.
- Department and service activity must not inflate hospital unique-patient totals.

## Printing
- Report data is prepared by the backend.
- Client printing uses the backend report manifest/envelope.
- Empty sections are printing-safe and may be omitted.
- Physical page counts remain the responsibility of the print engine.

## Release
Before release, run compile checks, client JavaScript syntax checks, unit/integration tests, clean-machine installation, LAN multi-client testing, backup/restore testing, and print verification.
