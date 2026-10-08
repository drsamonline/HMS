# Reporting / Print Batch 03

## Added report sections

- Billing / invoices
- Payments / receipts
- Medical documents
- MRD patient file and archive records

## Selection behavior

These sections respect the existing patient/case/admission context and optional date range. Billing uses invoice dates; payments are restricted to the invoices selected by the report context; medical documents use document dates; MRD returns patient-file index data and linked archive records.

## Printing boundary

The backend returns structured data. Rendering to PDF, preview, page selection, and Windows printer integration remain client responsibilities.
