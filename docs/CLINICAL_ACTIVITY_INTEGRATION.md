# Clinical Activity Integration

## Purpose

Connect existing Visit, Admission and Investigation records to the configurable Department/Service master without creating duplicate encounter systems.

## Optional classification

The new department, service and case-type fields are nullable so existing and partially completed records remain valid. Missing classification does not prevent saving or retrieval.

## Department/service rules

- A service belongs to exactly one department.
- Supplying a service without a department automatically resolves the department from the service.
- Supplying mismatched department and service values is rejected.
- Clearing a department also clears its service association.

## Clinical records

### Visit
Supports optional department, service and new/old case classification.

### Admission
Supports optional department, service and new/old case classification.

### Investigation
Supports optional department, service, new/old case classification and in-house/outsourced fulfillment.

## Statistics rule

These fields are classification data. They do not change the definition of a unique hospital patient. Hospital-wide patient totals must use distinct patient IDs; departmental/service reports may count their respective activities.

## Migration

Migration `0007_clinical_activity_integration` adds only nullable columns and indexes/foreign keys, preserving existing records.
