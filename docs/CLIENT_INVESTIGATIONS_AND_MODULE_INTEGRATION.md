# Client Clinical Module Integration — Batch 12

This batch wires the already-built Clinical and IPD client modules into the patient detail workspace and adds a functional investigations/laboratory/X-Ray workspace.

The investigation screen uses the existing configurable Department and DepartmentService masters. No department or laboratory category is hard-coded.

Supported actions:
- list patient investigations;
- create an investigation;
- choose department/service;
- classify new/old;
- classify in-house/outsourced;
- record or update investigation result;
- draft/verified/released result state.

Empty investigation and result lists are valid and do not block the patient workspace.

Printing remains downstream of the reporting/print-manifest system.
