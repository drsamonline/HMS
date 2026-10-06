# Department Service and Activity Foundation

HHMS departments remain master-editable. `DepartmentService` provides a configurable,
hierarchical service/subsection master. A service can have a parent service, allowing
structures such as Laboratory -> Hematology.

`ServiceActivity` is a generic activity ledger for department work that is not
adequately represented by a specialized clinical entity. It records the patient,
department, service, activity time, new/old classification, optional in-house/
outsourced fulfillment mode, and an optional source record.

This layer is deliberately separate from the statistics engine. Existing Visit,
Admission and Investigation records will be integrated with the reporting layer
after their department/service relationships are audited and extended minimally.
