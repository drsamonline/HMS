# Pharmacy Stock Safety — Batch 60

The active StockBatch workflow now applies expiry safety rules at the dispensing boundary.

## Statuses
- VALID: active stock with no expiry problem.
- EXPIRING_SOON: expiry falls within the requested warning window.
- EXPIRED: expiry date has passed.
- EXHAUSTED: no quantity remains.
- INACTIVE: batch is disabled.
- NO_EXPIRY: active stock without an expiry date.

Expired stock is rejected server-side before the atomic stock decrement. Client-side status display is advisory; the server remains authoritative.
