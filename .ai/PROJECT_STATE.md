# HHMS Project State

## Authoritative baseline
- Baseline source: user-provided HMS28.zip.
- Batch 58 is accepted as the pharmacy StockCard/atomic-adjustment layer.
- Current milestone: Batch 59 — Goods Receipt → Pharmacy Stock Integration.
- Current phase: Functional application build and cross-module integration.
- Comprehensive QA/debugging is not the primary phase.

## Locked workflow
1. Latest user-supplied ZIP is authoritative.
2. Never reconstruct the supplied baseline from GitHub/remote repositories unless explicitly requested.
3. Clean generated/stale transfer clutter before implementation.
4. Build functional code first; broad QA/debugging comes after functional completion.
5. Combine logically related work into the largest safe coherent batch.
6. Audit the generated batch ZIP before issuing `git add`.
7. Keep commit/push separate until GREEN.
8. Never delete source files based only on filename similarity.

## Pharmacy workflow — LOCKED
Medicine master → Purchase Order → Goods Receipt → StockBatch → StockCard → Dispensing.
- Goods Receipt is the authoritative inbound pharmacy-stock event.
- Receipt posting updates PO received quantities, creates StockBatch rows and StockCard receipt entries atomically.
- Dispensing decrements StockBatch and records StockCard issue atomically.
- Stock adjustments update StockBatch and StockCard atomically.
- General inventory StockTransaction remains separate from pharmacy batch stock.

## Data lifecycle — LOCKED
- Patient master remains live.
- Current operational year remains live.
- Years 2–5 are online read-only archives; years 6–10 are cold archives loaded on demand.
- New-year case renewal creates a new live case linked to its prior case family.
- Operational year may be calendar or configurable financial year.
- Clinical timestamps remain authoritative.
- Generic cleanup never deletes clinical/business records.
- Verified backup precedes high-risk maintenance.

## Remaining before QA
- Finish remaining IPD, laboratory, billing/MRD and frontend/reporting workflow continuity.
- Complete physical live-to-archive rollover migration.
- Complete packaging/deployment.
- Then comprehensive QA, security/performance/recovery testing and release validation.
