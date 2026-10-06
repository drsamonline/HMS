# Client Procurement Workspace — Batch 41

Functional procurement chain:

Supplier → Purchase Order → Goods Receipt → MedicineBatch.

Goods receipt validates remaining ordered quantity and posts the received medicine as a `MedicineBatch` in the same transaction.
