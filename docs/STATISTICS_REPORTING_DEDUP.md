# Hospital Statistics — Reporting & Deduplication

## Purpose

This milestone makes the statistics contract explicit:

- **Hospital unique-patient totals are distinct patients.**
- **Department/service totals are activity totals.**
- A patient may therefore appear once in the hospital total while contributing activity to several departments/services.

Example:

```text
Patient A
  OPD → Laboratory → X-Ray

Hospital unique patients = 1
OPD activity             = 1
Laboratory activity      = 1
X-Ray activity           = 1
```

## Canonical activity sources

The statistics service reads:

1. `Visit` — OPD activity.
2. `Admission` — IPD activity.
3. `Investigation` — investigation activity.
4. `ServiceActivity` — configurable department/service activity.

A `ServiceActivity` row carrying `source_type` and `source_id` for a canonical source is treated as a projection and excluded from the aggregate. This prevents the same Visit, Admission, or Investigation from being counted twice.

## Demographic rule

Hospital, department, and service demographic counts use **distinct patient IDs**. This means a patient with multiple activities in the same reporting scope is not counted repeatedly as male/female/child/adult.

New/old and fulfillment-mode counts remain **activity counts**, because those describe the individual clinical/service events rather than the permanent patient.

## Reporting period

`start_date` and `end_date` are inclusive. Internally the service uses:

```text
[start_date 00:00, day after end_date 00:00)
```

This avoids losing events occurring later on the end date.

## Current output

The hospital statistics response contains:

- hospital unique patients;
- total activities;
- OPD/IPD/investigation/service activity;
- distinct-patient demographics;
- new/old activity counts;
- in-house/outsourced investigation counts;
- department breakdown;
- service breakdown;
- daily breakdown.

## Deliberate non-goals

Printing, PDF generation, monthly/annual presentation layouts, dashboards, and frontend widgets remain separate milestones. This service is the backend reporting contract those later layers will consume.
