# Client Inventory Stock Balance — Batch 40

General inventory now maintains a transactional `quantity_on_hand` balance.

- Receipt increases balance.
- Return increases balance.
- Issue decreases balance.
- Adjustment applies its signed delta.
- A transaction that would make stock negative is rejected.
- The client displays current balance beside each inventory item and in the selected-item ledger.

This is the general inventory ledger and remains separate from pharmacy `StockBatch` dispensing.
