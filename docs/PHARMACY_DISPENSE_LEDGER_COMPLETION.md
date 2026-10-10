# Pharmacy Dispensing Ledger Completion — Batch 64

Dispensing now updates three pharmacy records in one transaction:

1. `StockBatch.quantity_remaining` decreases.
2. `DispenseRecord` records the issue.
3. `StockCard` records the same issue and post-transaction balance.

Expired stock is blocked at the server before the decrement.

`GET /stock-batches/medicine/{medicine_id}/status` exposes `AVAILABLE`, `EXPIRING_SOON`, `EXPIRED`, and `EXHAUSTED` states for active batches. The server remains authoritative for dispensing decisions.
