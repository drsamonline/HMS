# Batch 101 — Ward Occupancy Print Envelope & Operational Print Completion

> Status: **Completed** · Branch milestone: Batch 101 · Tests: 372 passing (see [../README.md](../../README.md))

## Purpose

Batch 99 shipped the OPD queue daily summary dashboard feed and explicitly left a
"future print envelope" hook; Batch 101 closes that hook and adds the missing
ward-level occupancy operational surface with its printable counterpart, completing
the operational reporting track (discharge audit → OPD queue → ward occupancy).

## Dashboard feed — `GET /dashboard/ward-occupancy-summary`

Complements the existing bed-level `/bed-occupancy` feed (Batch 83) with the
ward-level rollup administrators need.

Shared derivation pair (single source of truth for screen + paper):

- `build_ward_occupancy_summary_scan(db, limit)` — one bounded scan of active
  beds (`Bed.is_active`, ordered by ward/bed number, default limit 500, max 2000)
  plus one batched lookup of live admissions per bed. The Batch 61 partial unique
  index guarantees at most one active admission per bed, so counts cannot
  double-book. Length-of-stay days are computed against a single `as_of` snapshot
  inside the scan to keep the pure rollup deterministic.
- `build_ward_occupancy_summary_result(rows, as_of)` — pure per-ward bucketing:
  - Every bed lands in exactly one ward bucket; null/blank wards surface under the
    explicit `"Unassigned"` label (nothing disappears from the ledger).
  - Status vocabulary is case-insensitive; statuses outside
    occupied/reserved/available count toward the available remainder, keeping
    `occupied_beds + reserved_beds + available_beds == total_beds` true for any input.
  - Stay ages clamped non-negative; wards without a live admission report
    `longest_stay_days = None` rather than a fake zero.
  - Headlines: `wards_reported`, `total_beds`, `total_occupied`, `total_reserved`,
    `total_available`, `total_active_admissions`, with
    `active_admissions <= occupied_beds` ward-by-ward.

Schemas: `WardOccupancySummaryItem` / `WardOccupancySummaryResponse` in
`backend/app/schemas/dashboard.py`.

## Print envelope — `POST /reports/ward-occupancy-print-envelope`

- Request: `WardOccupancyPrintRequest` (`limit` ge=1 / le=2000 default 500, `title`).
- Service builder `build_ward_occupancy_print_envelope` delegates to the exact same
  `build_ward_occupancy_summary_scan` + `build_ward_occupancy_summary_result` pair,
  so printed headlines always match the dashboard feed ward-for-ward
  (screen/paper parity by construction).
- Envelope discriminator: `report_type = "ward_occupancy_print"`.
- Schemas: `WardOccupancyPrintRequest` / `WardOccupancyPrintLine` /
  `WardOccupancyPrintData` / `WardOccupancyPrintEnvelope` in
  `backend/app/schemas/reporting.py`.

The Batch 101 commit also carries the client-side renderer for the Batch 100
OPD queue summary envelope (`createOPDQueueSummaryPrintPreview`) — see
[CLIENT_BATCH100_SETTLEMENT_REFUND_AUDIT_PRINT_ENVELOPES.md](CLIENT_BATCH100_SETTLEMENT_REFUND_AUDIT_PRINT_ENVELOPES.md)
for the server-side queue/discharge envelope details.

## Client wiring

- `frontend/js/api.js`: `getDashboardWardOccupancySummary(options)` and
  `buildWardOccupancyPrintEnvelope(payload)`.
- `frontend/js/print.js`: `createOPDQueueSummaryPrintPreview(host, {envelope})`
  (per-day token ledger: waiting / in-consultation / completed / cancelled / open
  backlog) and `createWardOccupancyPrintPreview(host, {envelope})` (headline
  capacity table + per-ward occupancy ledger with longest-stay column). Both follow
  the envelope-first with raw `{data}` fallback signature convention.
- `frontend/js/reports.js`: "Ward occupancy summary" card (bounded Limit input,
  Prepare button posting through the envelope, headline aggregates reported in the
  status box) alongside the existing "OPD queue daily summary" card; both renderers
  and wrappers imported at module top.

## Contract tests

`backend/tests/test_batch101_ward_occupancy_print_envelope.py` (10 tests):
pure-derivation invariant round-trips (status split, Unassigned bucketing,
negative-stay clamp, empty scan, None-longest-stay), schema exports/bounds/
discriminator, route registration on the app object, service reuse of the shared
builders, frontend wrapper/renderer/card wiring, and documentation indexing.

## Invariants recap

| Invariant | Scope |
| --- | --- |
| `occupied_beds + reserved_beds + available_beds == total_beds` | every ward row |
| `total_occupied + total_reserved + total_available == total_beds` | headlines |
| `active_admissions <= occupied_beds` | every ward row |
| `wards_reported == len(items)` | headlines |
| Printed data == dashboard data (same scan/derivation) | screen/paper parity |
