# Number Sequence Integration

Operational identifiers are now generated from the editable `NumberSequence` master inside the same transaction as the business record.

Integrated identifiers:
- patient number
- visit number
- case number
- admission number
- discharge number
- prescription number
- investigation number
- invoice number
- receipt number

The client can configure prefixes, suffixes, padding, active status and reset frequency through the existing settings workflow. OPD queue token numbering remains date-aware in its dedicated queue service.
