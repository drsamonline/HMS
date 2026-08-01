# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository structure
- Project documentation foundation

## [0.0.1] - 2025-01-30

### Added - Session 001
- Repository initialization
- Project constitution and rules
- Documentation templates
- Directory structure (11 root folders)
- Core documentation files (README, LICENSE, ROADMAP, etc.)
- AI context files (PROJECT_CONSTITUTION, PROJECT_STATE, etc.)

### Added - Session 002 (FND-002)
- Enhanced directory structure:
  - .github/ISSUE_TEMPLATE/
  - docs/ subfolders (01_Project through 10_Release_Notes)
  - backend/app/, backend/tests/
  - frontend/src/, frontend/public/
  - database/schema/, database/migrations/
  - scripts/setup/, scripts/backup/
  - assets/logos/, assets/icons/, assets/screenshots/
  - templates/print/, templates/reports/
  - tools/dev/
- Documentation standards:
  - docs/INDEX.md - Documentation navigation
  - docs/GLOSSARY.md - Terminology definitions
  - docs/NAMING_CONVENTIONS.md - Naming standards
  - docs/UI_GUIDELINES.md - UI design guidelines (placeholder)
  - docs/PRINT_STANDARDS.md - Printing standards
  - docs/VALIDATION_RULES.md - Validation rules (placeholder)
- AI governance enhancements:
  - .ai/PROJECT_INDEX.md - Repository navigation guide
  - .ai/MODULE_STATUS.md - Module progress dashboard
- Updated all session tracking files

### Added - Session 003 (SPEC-001)
- Master Specification document:
  - docs/MASTER_SPECIFICATION.md - Complete scope definition for HHMS v1.0
  - Project purpose and objectives
  - Scope boundaries (included/excluded features)
  - 12 modules documented with purposes and functions
  - Navigation structure defined
  - Complete screen inventory (60+ screens)
  - Database entity list (27 entities)
  - 8 major workflows documented
  - 6 user roles with responsibilities
  - Report catalog (8 categories, 30+ reports)
  - Printable documents list
  - "Planned After Version 1" section (10 feature categories)
- Scope officially FROZEN for Version 1.0

### Added - Session 004 (SPEC-001-FINAL)
- Master Specification finalized in compact format:
  - Concise one-paragraph purpose
  - Simplified scope lists
  - 12 modules with 4 bullet points each maximum
  - Navigation menu (12 items)
  - Screens listed by module (names only)
  - User roles (one line each)
  - Reports list (names only)
  - Print documents list (names only)
  - Future version features (list only)
- Document optimized to ~8-10 pages equivalent
- Milestone 0 marked as COMPLETE (100%)

### Changed
- PROJECT_STATE.md updated to reflect Session 003 progress
- PROGRESS.md updated to 90% completion for Milestone 0
- TODO.md expanded with SPEC-001 completion notes
- SESSION_LOG.md added Session 003 entry

### Changed - Session 004
- PROJECT_STATE.md: Status changed to COMPLETE, next task is Milestone 1
- PROGRESS.md: Milestone 0 now at 100% completion
- TODO.md: Added specification section, noted Milestone 0 completion
- SESSION_LOG.md: Added Session 004 entry


## [0.0.1] - 2025-01-30

### Session 004 - Database Schema Design (DB-002)

#### Added
- docs/DATABASE_ENTITIES.md - Frozen entity list with 35 entities
- docs/DATABASE_SCHEMA.md - Complete relational database schema

#### Changed
- Updated .ai/PROJECT_STATE.md - Marked DB-002 complete
- Updated .ai/PROGRESS.md - Database design phase complete
- Updated .ai/TODO.md - Added completed database design tasks
- Updated .ai/SESSION_LOG.md - Added Session 004 details

#### Details
- Defined all 35 tables with columns, primary keys, foreign keys, and indexes
- Applied snake_case naming convention throughout
- Added created_at/updated_at timestamps to all tables
- Added is_active flag only to master/configuration tables
- Validated no circular dependencies
- Achieved ~3NF normalization

#### Module Breakdown
- Core: 3 tables (User, Role, AuditLog)
- Patients: 2 tables (Patient, Guardian)
- Clinical: 3 tables (Consultation, Diagnosis, ClinicalNote)
- Prescription: 2 tables (Prescription, PrescriptionItem)
- Pharmacy: 3 tables (Medicine, DispenseRecord, StockAdjustment)
- Inventory: 6 tables (Supplier, StockBatch, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, StockCard)
- Billing: 3 tables (Invoice, InvoiceItem, Payment)
- IPD: 6 tables (Ward, Room, Bed, Admission, Discharge, BedAssignment)
- MRD: 2 tables (PatientFile, ArchiveRecord)
- Administration: 2 tables (Department, Designation)
- Settings: 3 tables (Hospital, SystemSetting, NumberSequence)

### Session 003 - Master Specification (SPEC-001)

#### Added
- docs/MASTER_SPECIFICATION.md - Complete functional specification for v1.0

#### Changed
- Updated all project state tracking files
- Froze scope for Version 1.0

#### Details
- Defined 12 modules with purposes and functions
- Listed 60+ screens grouped by module
- Identified 6 user roles with responsibilities
- Listed 30+ reports across 8 categories
- Defined 9 printable document types
- Moved advanced features to "Planned After Version 1"

### Session 002 - Repository Standardization (FND-002)

#### Added
- docs/ subdirectories (01_Project through 10_Release_Notes)
- backend/app/, backend/tests/
- frontend/src/, frontend/public/
- database/schema/, database/migrations/
- scripts/setup/, scripts/backup/
- assets/logos/, assets/icons/, assets/screenshots/
- templates/print/, templates/reports/
- tools/dev/
- .github/ISSUE_TEMPLATE/
- docs/INDEX.md
- docs/GLOSSARY.md
- docs/NAMING_CONVENTIONS.md
- docs/UI_GUIDELINES.md
- docs/PRINT_STANDARDS.md
- docs/VALIDATION_RULES.md
- .ai/PROJECT_INDEX.md
- .ai/MODULE_STATUS.md

#### Changed
- Updated all project state tracking files

### Session 001 - Repository Initialization (FND-001)

#### Added
- Initial directory structure (11 directories)
- Root documentation files (README.md, LICENSE, CHANGELOG.md, ROADMAP.md, CONTRIBUTING.md, SECURITY.md, VERSION, .gitignore, .editorconfig)
- AI context files (.ai/PROJECT_CONSTITUTION.md, .ai/PROJECT_STATE.md, .ai/AI_CONTEXT.md, .ai/CODING_RULES.md, .ai/PROGRESS.md, .ai/TODO.md, .ai/SESSION_LOG.md, .ai/DECISIONS.md, .ai/PROMPTS.md, .ai/QWEN_RULES.md, .ai/REVIEW_CHECKLIST.md)

#### Details
- MIT License applied
- Version set to 0.0.1
- Project constitution locked with 12 principles
- Roadmap defined with 8 milestones (0-7)
