# Pharmacy Stock Card Ledger — Batch 57

HHMS now maintains an immutable stock-card ledger for each pharmacy StockBatch.

## Workflow

Receipt/return/issue/adjustment → atomic StockBatch balance update → StockCard entry.

Dispensing creates the DispenseRecord and its corresponding `StockCard` issue entry in the same database transaction.

## Safety

- Stock can never become negative through an issue or adjustment.
- The stock-card entry records the post-transaction balance.
- Dispensing and its stock issue ledger are committed atomically.
- Existing generic `StockTransaction` remains the ledger for non-pharmacy InventoryItem records.
- No clinical/business data is deleted or rewritten.
