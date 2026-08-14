# Client MRD Medical Documents

The MRD workspace now manages `MedicalDocument` records alongside the existing patient-file and archive records.

## Supported operations

- list documents for a patient;
- create a document metadata record;
- retrieve a document record;
- update document metadata.

The current client records metadata and file references. Actual binary file upload/storage remains separate from this batch.

The authenticated user is the authoritative `uploaded_by` value on create.
