# Client Unified Dashboard & Navigation — Batch 17

## Scope

Adds a lightweight client dashboard, recent-patient shortcuts, and a unified entry point for Patients, Statistics, and Reports/Printing.

## Design

The dashboard is client-only and uses existing backend APIs. It does not introduce a duplicate backend dashboard model.

Recent patients are stored only in the authenticated browser session and are not persisted as new medical data.

Global application navigation remains separate from patient-specific record tabs.

## Empty-state behavior

No recent patients is a valid state. Dashboard loading failures for recent-patient shortcuts do not prevent the rest of the dashboard from opening.
