# HHMS Department Master

The Department master is the authoritative editable list of hospital departments.
It is intentionally separate from department-level service statistics.

## Current fields

- code
- name
- description
- department type
- active status
- audit timestamps

Departments are managed through the authenticated API and are not hard-coded into
statistics or frontend navigation.

## Statistics relationship

A later statistics/service milestone will add the minimum required links between
clinical encounters, departmental services, and departments. Hospital-wide patient
counts will use distinct patient identities; departmental totals will represent
activity and must not be added together as unique hospital-patient totals.

## API

- `GET /api/v1/departments`
- `POST /api/v1/departments`
- `GET /api/v1/departments/{department_id}`
- `PATCH /api/v1/departments/{department_id}`
