# Pharmacy Stock Card Ledger

Each pharmacy StockBatch movement produces an immutable StockCard entry. Receipt, dispensing and manual adjustments share the same transaction boundary as the StockBatch balance change.

StockCard is append-only through the service layer. Historical rows are not edited or deleted by routine inventory operations.

General inventory StockTransaction remains a separate subsystem.
