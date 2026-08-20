# Billing Atomic Consistency — Batch 68

This batch closes concurrency and derived-status gaps in the billing workflow.

- Payment creation locks the invoice row before calculating outstanding balance.
- Invoice payment status is derived from recorded payments; clients cannot directly set it during invoice update.
- Paid and cancelled invoices cannot be changed through invoice-item operations.
- Adding/removing invoice items recalculates the invoice total and derives payment status from the already-recorded payments.
- Removing an item is blocked when the resulting invoice total would be lower than the amount already paid.

These rules are business-logic protections. Broad concurrency/performance/security testing remains part of the later comprehensive QA phase.
