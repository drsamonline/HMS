# Goods Receipt → Pharmacy Stock Integration — Batch 59

Flow:

Purchase Order → Goods Receipt → StockBatch → StockCard RECEIPT

The posting is atomic. Goods-receipt lines, cumulative purchase-order receipt quantities, StockBatch rows and StockCard entries commit together or roll back together.

Rules:
- Supplier must match the purchase order.
- Each receipt line must belong to the selected purchase order.
- Medicine must match its purchase-order item.
- Quantity cannot exceed the outstanding purchase-order quantity.
- A purchase-order line cannot be repeated within one receipt.
- Purchase order becomes `PartiallyReceived` or `Received` from cumulative quantities.
- Each received line creates a StockBatch and a `RECEIPT` StockCard entry.
