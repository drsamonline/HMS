# Client Billing + MRD Workspace

## Scope

This batch connects the patient workspace to the existing billing and medical-record APIs.

## Billing

The client lists patient invoices, creates invoices, lists invoice payments, and records payments. Empty billing data is a valid state and does not block the patient workspace.

## MRD

The client lists patient files, creates a patient file, and loads archive records for those files. Empty MRD data is a valid state.

## Boundary

The client does not duplicate invoice, payment, patient-file or archive models. It uses the existing backend contracts.
