# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Sessions are listed newest-first within each release; batch entries reflect the
functional build batches tracked in [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md).

## [Unreleased]

### Added — Batch 70 · Encounter Annual Lifecycle & Rollover
- Visit lifecycle metadata (`visit_year`, `storage_tier`, `is_current_year`) derived from the encounter date at creation, honoring the configured operational year.
- Alembic migration `0021_visit_operational_year_lifecycle` with backfill of existing visit rows.
- Permanent `VisitArchiveReference` records so visit identity survives physical live-database removal.
- Annual rollover now physically archives completed-year visits alongside cases (children detached first, post-rollover validation extended to visits).
- Historical archived-visit read endpoint `/maintenance/archives/{year}/patients/{patient_id}/visits` and client API wrapper `getHistoricalArchiveVisits`.
- Contract test suite `backend/tests/test_visit_archive_rollover.py` (7 tests; full suite 149 passed).

### Added — Batch 69 · Annual Case Rollover
- Verified pre-rollover backup and administrator-only annual case rollover.
- Permanent `CaseArchiveReference` records for cases physically removed from the live database.
- Archived-case lineage preserved through `case_family_id` and the verified annual archive snapshot.
- Safe removal of direct case children (`Diagnosis`, `FollowUp`) before removing archived `CaseRecord` rows.
- Live `renewed_from_case_id` references cleared when they would point at physically archived cases.
- Rollover preview and execution API endpoints.
- Rollover action in the System Health & Data Lifecycle workspace.
- See [docs/ANNUAL_CASE_ROLLOVER.md](docs/ANNUAL_CASE_ROLLOVER.md).

## [0.0.1] - 2025-01-30

Foundation phase (Milestone 0) — repository initialization, standards, specification, and database design.

### Added — Session 004 · Database Schema Design (DB-002)
- [docs/DATABASE_ENTITIES.md](docs/DATABASE_ENTITIES.md) — frozen entity list with 35 entities.
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) — complete relational database schema.
- All 35 tables defined with columns, primary keys, foreign keys, and indexes.
- `snake_case` naming throughout; `created_at`/`updated_at` on all tables; `is_active` only on master/configuration tables.
- No circular dependencies; ~3NF normalization achieved.
- Module breakdown: Core 3 · Patients 2 · Clinical 3 · Prescription 2 · Pharmacy 3 · Inventory 6 · Billing 3 · IPD 6 · MRD 2 · Administration 2 · Settings 3.

### Added — Session 004 · Master Specification Finalized (SPEC-001-FINAL)
- Master Specification finalized in compact format (~8–10 pages equivalent):
  one-paragraph purpose, simplified scope lists, 12 modules (≤4 bullets each),
  12-item navigation menu, screens by module, one-line role descriptions,
  report and print-document lists, future-version feature list.
- Milestone 0 marked COMPLETE (100%).

### Added — Session 003 · Master Specification (SPEC-001)
- [docs/MASTER_SPECIFICATION.md](docs/MASTER_SPECIFICATION.md) — complete scope definition for HHMS v1.0:
  project purpose and objectives, scope boundaries (included/excluded),
  12 modules with purposes and functions, navigation structure,
  full screen inventory (60+ screens), database entity list (27 entities),
  8 major workflows, 6 user roles, report catalog (8 categories, 30+ reports),
  printable documents list, and a "Planned After Version 1" section (10 feature categories).
- Scope officially **FROZEN** for Version 1.0.

### Added — Session 002 · Repository Standardization (FND-002)
- Directory structure:
  `.github/ISSUE_TEMPLATE/`, `docs/` subfolders (01_Project → 10_Release_Notes),
  `backend/app/`, `backend/tests/`, `frontend/src/`, `frontend/public/`,
  `database/schema/`, `database/migrations/`, `scripts/setup/`, `scripts/backup/`,
  `assets/logos/`, `assets/icons/`, `assets/screenshots/`,
  `templates/print/`, `templates/reports/`, `tools/dev/`.
- Documentation standards:
  [docs/INDEX.md](docs/INDEX.md), [docs/GLOSSARY.md](docs/GLOSSARY.md),
  [docs/NAMING_CONVENTIONS.md](docs/NAMING_CONVENTIONS.md),
  [docs/UI_GUIDELINES.md](docs/UI_GUIDELINES.md),
  [docs/PRINT_STANDARDS.md](docs/PRINT_STANDARDS.md),
  [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md).
- AI governance: `.ai/PROJECT_INDEX.md`, `.ai/MODULE_STATUS.md`.

### Added — Session 001 · Repository Initialization (FND-001)
- Initial directory structure (11 root folders).
- Root documentation: `README.md`, `LICENSE` (MIT), `CHANGELOG.md`, `ROADMAP.md`
  (8 milestones, 0–7), `CONTRIBUTING.md`, `SECURITY.md`, `VERSION` (0.0.1),
  `.gitignore`, `.editorconfig`.
- AI context files in `.ai/`: project constitution (12 locked principles),
  coding rules, decisions, state tracking, review checklist, prompts.

### Changed
- `.ai/` session-tracking files (PROJECT_STATE, PROGRESS, TODO, SESSION_LOG)
  updated after each session to reflect current status.
