# Batch 51 — Data Lifecycle, Case Renewal & System Maintenance

This batch adds the first functional layer of the final HHMS operational data-lifecycle model:

- current-year live case continuity;
- yearly case renewal with stable case-family linkage;
- online/cold archive manifest tracking;
- verified annual SQLite archive snapshots;
- read-only historical case retrieval by year;
- safe runtime maintenance;
- database health metrics;
- automatic safe maintenance scheduling;
- administrator-triggered database vacuum;
- retention policy visibility.

It deliberately does not let generic cleanup delete clinical or business data.
