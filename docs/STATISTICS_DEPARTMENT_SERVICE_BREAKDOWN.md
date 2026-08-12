# Statistics — Department and Service Breakdown

This batch exposes the configurable master classifications already present in
the Department and DepartmentService masters to the statistics response.

## Department

Every department statistic includes `department_type`, for example:

- clinical
- diagnostic
- support
- administrative
- financial

The department master remains editable; statistics do not hard-code hospital
departments.

## Service

Every service statistic includes `service_type`. This can be used by the
hospital master to classify subsections such as:

- hematology
- biochemistry
- clinical pathology
- microbiology
- x-ray
- physiotherapy
- OGA

The service also reports OPD, IPD, investigation and generic-service activity
counts, so a service can be analysed without confusing activity counts with
unique-patient counts.

## Deduplication

`unique_patient_count` remains a distinct-patient measure. Activity counts are
not deduplicated because they represent work performed by the department or
service.

For example, one patient can contribute one hospital unique patient while
contributing separately to OPD, laboratory and X-ray activity.
