# Billing Integrity — Batch 67

## Locked workflow

`Invoice -> Invoice Items -> Payments -> Balance/Status`

Billing operations that can change the invoice total are synchronized with payment totals.

## Rules

- Invoice and payment datetimes must be timezone-aware.
- A fully paid invoice cannot be modified.
- Payment creation locks the invoice row during balance calculation and update.
- Payments cannot exceed the current outstanding balance.
- Adding/removing invoice items recalculates the invoice total and then derives payment status from recorded payments.
- Removing an invoice item is rejected when the resulting invoice total would be lower than payments already received.

No historical payment or invoice record is deleted automatically.
