# Client Pharmacy Workspace

This batch adds pharmacy/dispensing UI using existing medicine, stock-batch, prescription and dispensing APIs.

## Workflow

Patient → Clinical → Pharmacy → Prescription item → Stock batch → Dispense.

The client validates that dispensing does not exceed the currently reported stock batch quantity. The server remains authoritative.

No stock transaction model is duplicated in the client.
