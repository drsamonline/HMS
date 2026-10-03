# Client Clinical Records — Batch 10

This batch connects the patient workspace to the existing clinical backend.

## Supported client records

- Case records: list, create and update.
- Diagnosis: list and create.
- ICD-11: on-demand search through the HHMS backend.
- Follow-ups: list and create.
- Prescriptions: create, using the existing medicine master.
- Quick Generals and Modalities remain JSON-backed compact structured data.
- Narrative case sections remain free-text.

The client does not duplicate diagnosis, ICD-11, follow-up or prescription data inside the case record.

## Empty-data behavior

No existing case is required to open the workspace. A patient can create a draft case first. Diagnosis, prescription and follow-up panels remain available only after a case exists. Empty optional values are omitted from request payloads where possible.
