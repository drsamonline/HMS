# HHMS Reporting & Print-Data Foundation

## Purpose

This milestone prepares structured clinical data for preview and printing. It does not render PDF or invoke Windows printers.

## Supported selection

The clinical report endpoint can select:

- patient demographics
- homoeopathic case record
- diagnoses / ICD-11
- follow-ups
- prescriptions
- investigations
- IPD assessment
- pain assessments
- nutritional assessment
- diet charts
- progress notes
- discharge summary

An empty section list means the complete supported clinical scope is requested.

## Scope

A report can be selected by:

- patient ID
- case record ID
- admission ID
- optional inclusive start/end datetime

The service resolves the patient and validates that a requested case/admission belongs to that patient.

## Endpoint

`POST /api/v1/reports/clinical-data`

The response is structured JSON intended for a future preview/print renderer.

## Printing boundary

Rendering remains a client concern. The future HHMS client will use this data to support:

- complete case printing
- selected case sections
- individual clinical documents
- page/document-specific printing
- date-range/batch printing

No PDF library or printer dependency is added to the backend in this milestone.
