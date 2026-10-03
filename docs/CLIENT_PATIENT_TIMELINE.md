# Client Patient Timeline

The patient Overview tab now presents a longitudinal timeline assembled from existing backend resources.

## Included sources

- OPD visits
- IPD admissions
- Investigations
- Billing invoices
- MRD patient files

The timeline is a client presentation layer. It does not create a new database table or duplicate clinical data.

## Empty data

Missing records are valid. The overview remains usable and displays an explicit empty state.

## Next integration

Case-level follow-ups and detailed clinical events remain available through the Clinical workspace. They are not duplicated into the timeline until a backend patient-wide case endpoint is justified.
