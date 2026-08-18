# Unified Patient History — Batch 55

## Purpose
Provide a single longitudinal patient timeline while keeping archive databases detached from normal live operation.

## Behavior
- Current-year activity remains live and loads normally.
- Verified historical archive years are selectable on demand.
- Selecting a year loads only that year's archived case records.
- Archived case records are displayed as read-only history.
- Patient master data remains live regardless of encounter age.
- Calendar-year and financial-year operational-year rules remain authoritative through the existing operational-year API.

## Safety
This client workflow does not edit, merge, delete, or relocate historical clinical data. Physical rollover/archival remains controlled by the server maintenance/lifecycle subsystem.
