# Client Dashboard — Outstanding Billing Continuity (Batch 82)

Turns the billing service's oldest-first outstanding-invoice feed into an
actionable administrative receivables panel on the HHMS client dashboard,
mirroring the Batch 79 due-follow-up continuity pattern for the billing side.

## Backend contract

### Service layer — `backend/app/services/billing.py`

- `BillingService.list_outstanding_invoices(db, limit)` returns
  `(invoices, total_balance)`.
- Candidate selection uses `Invoice.payment_status.in_(("unpaid", "partial"))`
  ordered `Invoice.invoice_date.asc()` (oldest first, chase-up priority).
- Balances are **derived from live payments** via
  `func.coalesce(func.sum(Payment.amount_paid), 0)` per invoice — never taken
  from a stale stored status alone — and cancelled/paid invoices never surface.

### Endpoint — `backend/app/api/v1/endpoints/dashboard.py`

- `GET /api/v1/dashboard/outstanding-invoices?limit=` (authenticated;
  `limit` 1–200, default 100).
- Each row is enriched with actionable identity: patient name/number (batched
  lookup, no N+1), invoice number/date, `total_amount`, derived `amount_paid`
  (clamped to the invoice total), `balance_due` (never negative),
  `payment_status`, and `days_outstanding` computed against today.
- Response schemas `OutstandingInvoiceItem` / `OutstandingInvoicesResponse`
  (`backend/app/schemas/dashboard.py`) expose `as_of`, `items`,
  `total_outstanding`, and `invoice_count`.
- Reconciliation invariant: `balance_due + amount_paid == total_amount`
  for every item.

## Frontend wiring

- API wrapper `getDashboardOutstandingInvoices(options)` in
  `frontend/js/api.js`.
- `frontend/js/dashboard.js` renders an **"Outstanding invoices"** panel:
  - summary line with invoice count and formatted total outstanding,
  - one card per invoice showing patient name, invoice number, balance of
    total, and age in days,
  - clicking a card navigates to the patients view and dispatches
    `hhms:open-patient` for direct handoff into the patient workspace,
  - graceful "unavailable right now" state on fetch failure (same pattern as
    the due-follow-ups panel).

## Tests

- Contract suite: `backend/tests/test_dashboard_outstanding_invoices.py`
  (service feed, endpoint wiring, schemas, frontend wrapper/panel).
- Full backend suite green after this batch: **222 passed**.
