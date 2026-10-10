# Pharmacy Dispensing Stock Integrity

Dispensing is a transactional operation.

The server:

1. Resolves the prescription item.
2. Confirms the requested medicine matches the prescription.
3. Resolves the selected stock batch.
4. Confirms the batch belongs to the medicine and is active.
5. Calculates the remaining prescribed quantity from previous dispense records.
6. Rejects quantities above the remaining prescription quantity.
7. Atomically decrements `StockBatch.quantity_remaining`.
8. Creates the `DispenseRecord` using the authenticated user identity.
9. Commits both operations together.

The stock decrement uses a conditional SQL `UPDATE` so concurrent requests cannot dispense more than the available quantity.

The client may continue to send `dispensed_by` for backwards compatibility, but the server does not trust it; the authenticated token identity is authoritative.

No database migration is required because this batch changes transactional behavior only.
