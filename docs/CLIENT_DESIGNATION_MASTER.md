# Client Designation Master — Batch 37

The administration client can now consume the editable staff-designation master through:

- `GET /api/v1/designations`
- `POST /api/v1/designations`
- `GET /api/v1/designations/{designation_id}`
- `PATCH /api/v1/designations/{designation_id}`

The designation master is data-driven and uses the existing `DesignationType` values. The server remains authoritative for validation and persistence.
