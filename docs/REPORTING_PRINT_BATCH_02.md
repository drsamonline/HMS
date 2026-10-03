# Reporting & Print-Data Batch 02

## Scope

This batch extends the reporting foundation with a report catalog, explicit admission-section selection, and date-range batch case reporting.

## Report catalog

`GET /api/v1/reports/catalog` returns the supported clinical sections so a client can construct print/preview selectors without hard-coded labels.

## Partial reports

`admission` is now an explicit selectable section. Admission data is returned only when that section is selected (or when the request asks for the complete supported report scope).

## Batch case reports

`POST /api/v1/reports/clinical-data/batch` accepts a datetime range, optional patient ID, optional case status, selected sections, and a safety limit. It returns structured report packets for cases created in that period.

The endpoint is intended for date-wise and period-wise batch preview/printing. The backend still does not render PDF or invoke a printer.

## Printing boundary

The client remains responsible for preview/rendering/Windows printing. The backend supplies complete or partial structured clinical report packets.
