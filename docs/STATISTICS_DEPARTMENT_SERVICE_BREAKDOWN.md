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


## Reporting dimensions

The hospital response also exposes report-level breakdowns for:
- activity type: OPD, IPD, investigation, configurable service;
- case type: new, old, unspecified;
- investigation fulfillment: in-house, outsourced, unspecified;
- configurable service type/category with both activity and unique-patient counts.

These breakdowns remain separate from the deduplicated hospital patient total.


## Batch 05 correctness hardening

Department and service demographic counts are computed within each grouped department/service scope. The previous full-scope aggregate pattern could repeat hospital-wide demographic counts for every department/service. Department aggregation also no longer selects an ungrouped service-type column.
