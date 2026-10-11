# Demo Data (Out-of-the-Box 2025 Dataset)

Status: Active

HHMS can bootstrap a realistic demo dataset so a fresh install is immediately
usable — dashboards, reports, print envelopes, pharmacy stock and billing all
show populated figures without manual data entry.

## What gets seeded (year 2025)

| Area | Volume | Notes |
|------|--------|-------|
| Staff users | admin + doctors + pharmacist + billing clerk | created through the service layer with proper roles |
| Masters | departments, services, designations, ~25 homeopathic medicines | medicines carry batches + opening stock with valid expiry dates |
| Beds | wards with beds | bed census feeds are non-empty |
| Patients | 40 registrations spread Jan–Dec 2025 | sequential patient numbers from the hospital number sequences |
| Visits / OPD tokens | 120 visits with token queue entries | OPD queue dashboard populated |
| Case records & prescriptions | 120 prescriptions with items | case/prescription numbers minted via the normal sequence services |
| Dispenses | ~240 ledger-backed dispense rows | pharmacy stock ledger stays balanced (receipts − dispenses = balance) |
| Investigations | 40 orders with verified results | lab backlog + billing reconciliation feeds populated |
| IPD admissions | 8 admissions with discharges | ward occupancy + discharge audit feeds populated |
| Invoices & payments | 128 invoices, 118 payments | mix of settled, outstanding and overpaid — receivables/collection reports show real figures |

All transactional dates fall inside the requested year so operational-year
statistics and every reporting/print envelope render meaningful numbers.

## How to seed

From the backend directory (`backend/`):

```bash
# One-shot OOBE command (bootstraps migrations + default admin, then seeds):
python -m app.server seed-demo-data [--year 2025] [--force]

# Equivalent standalone module invocation:
python -m app.cli.seed_demo_data [--year 2025] [--force]
```

Or automatically at server startup by exporting the environment flag:

```bash
HHMS_SEED_DEMO_DATA=true python -m app.server
```

The env-flag path never blocks boot: if seeding fails the server still starts
(the error is logged).

## Safety and idempotency

- **Idempotent** — a `SystemSetting` marker (`demo_data_seeded_<year>`) is
  written after a successful run; re-running is a no-op unless `--force`.
- **Refuses dirty databases** — seeding aborts if the target database already
  contains real transactional data (patients/invoices), unless `--force` is
  given. Never point it at a production database you care about without
  reviewing that guard.
- **Service-layer writes only** — the seeder goes through the same services as
  the API (number sequences, stock ledger, invoice balances, audit log), so
  integrity invariants hold on seeded data exactly as on operator-entered data.

## Resetting / regenerating

To start clean, delete the runtime database and re-run the seeder:

```bash
rm -f data/hhms.sqlite3 data/hhms.sqlite3-wal data/hhms.sqlite3-shm
cd backend && python -m app.server seed-demo-data
```

(Back up first if the database may contain work you want to keep — see
[ADMIN_TRAINING.md](ADMIN_TRAINING.md) for the backup/restore drill.)

Default login after a fresh bootstrap: `admin` / `admin` (change immediately —
see [SECRET_ROTATION_RUNBOOK.md](SECRET_ROTATION_RUNBOOK.md) for production
hardening steps).
