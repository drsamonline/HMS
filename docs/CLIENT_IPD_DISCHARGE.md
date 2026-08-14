# Client IPD Discharge

Batch 34 completes the active-admission discharge workflow in the client.

- Select an active admission.
- Enter discharge date/time, summary and remarks.
- The authenticated user is sent as `discharged_by`.
- The existing backend discharge transaction changes the admission to discharged and releases the bed.
- Active admissions refresh after discharge.
