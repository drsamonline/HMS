# HHMS Hospital Statistics Engine

## Purpose

The statistics engine provides date-range hospital statistics without confusing
unique hospital patients with departmental/service activity.

## Counting rules

### Unique hospital patients

The hospital total is the number of distinct `patient_id` values appearing in
the reporting-period activity scope.

A patient who has an OPD visit, laboratory investigation and X-Ray remains one
hospital patient.

### Activity totals

Activities are counted independently:

- OPD = Visit
- IPD = Admission
- Investigation = Investigation
- Generic service = ServiceActivity for configurable services

Therefore one patient can contribute multiple departmental activities while
remaining one unique hospital patient.

### ServiceActivity projection rule

If a `ServiceActivity` row has `source_type` and `source_id` identifying a
Visit, Admission or Investigation, it is treated as a projection of that
canonical source and excluded from aggregate counts. This prevents a source
record and its activity projection from being counted twice.

Generic `ServiceActivity` rows without a canonical source projection remain
countable for departments such as Physiotherapy, OGA, or future configurable
departments.

## Demographic breakdown

The current report provides:

- male
- female
- other/unspecified gender
- child: age below 18
- adult: age 18 or above
- unspecified age

These are patient-level counts for hospital totals and activity-level counts
for department/service breakdowns.

## Case classification

`new`, `old`, and unspecified are supported. Missing values are not rejected
and are reported as unspecified.

## Investigation fulfillment

Investigation activity recognizes:

- `inhouse`
- `in-house`
- `in_house`
- `outsourced`

as the corresponding fulfillment categories.

## Endpoint

`GET /statistics/hospital`

Required:

- `start_date`
- `end_date`

Optional:

- `department_id`
- `service_id`
