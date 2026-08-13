# Reporting / Print Batch 04

Adds a print-envelope endpoint that packages a selected clinical report with print metadata. The client remains responsible for rendering, preview, page layout, PDF export, and Windows printing.

Endpoint: `POST /api/v1/reports/clinical-data/print-envelope`

The envelope includes report title, generation time, patient/context identifiers, selected sections, available sections, and the structured clinical report.
