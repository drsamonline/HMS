# HHMS Documentation Index

---

## 1. Document Information

| Field | Value |
|-------|-------|
| **Title** | HHMS Documentation Index |
| **Document ID** | HHMS-DOC-001 |
| **Version** | 1.0.0 |
| **Status** | Frozen |
| **Author** | Dr. Sohil Momin |
| **Date** | 31 July 2026 |

---

## 2. Purpose

This document serves as the **master index** for all Homeopathic Hospital Management System (HHMS) documentation. It provides a centralised reference point for navigating project specifications, database design, coding standards, and development workflow guidelines.

All contributors, reviewers, and stakeholders should begin their engagement with the HHMS project by consulting this index to locate the appropriate documentation for their role and current task.

---

## 3. Project Overview

HHMS is a comprehensive management system purpose-built for homeopathic hospitals and clinics. The system provides integrated tools for:

- **Patient Management** — registration, records, and history tracking
- **Consultation Recording** — structured clinical notes and case documentation
- **Prescription Generation** — homeopathic remedy selection with dosage and potency management
- **Administrative Operations** — scheduling, billing, inventory, and reporting

The system is designed with the following core objectives:

- **Offline-first architecture** for environments with limited or intermittent connectivity
- **Modular design** enabling independent development, testing, and deployment of features
- **Data portability and security** ensuring patient information remains protected and transferable
- **Print-ready output** for prescriptions, reports, and administrative documents

---

## 4. Documentation Principles

All HHMS documentation adheres to the following principles:

1. **Single Source of Truth** — Each concept, entity, or rule is defined in exactly one document. Other documents reference it rather than duplicate it.

2. **Specification Before Implementation** — All features, schemas, and behaviours are fully documented before any code is written. Documentation drives development, not the reverse.

3. **Precision and Completeness** — Documents must be unambiguous, self-contained, and sufficient for a developer to implement against without requiring verbal clarification.

4. **Living Documents** — Documentation is versioned and maintained alongside the codebase. Changes to specifications must be reflected in the relevant document before implementation proceeds.

5. **Consistent Structure** — All documents follow a uniform format with document metadata, clear section headings, and standardised terminology.

6. **No Assumptions** — Documents explicitly state all requirements, constraints, and edge cases. Implicit knowledge is avoided.

---

## 5. Documentation Reading Order

The following reading order is recommended for new contributors and reviewers:

| Order | Document | Audience |
|-------|----------|----------|
| 1 | INDEX.md | All |
| 2 | MASTER_SPECIFICATION.md | All |
| 3 | DATABASE_ENTITIES.md | Backend, Database |
| 4 | DATABASE_SCHEMA.md | Backend, Database |
| 5 | CODING_STANDARDS.md | Developers |
| 6 | DEVELOPMENT_ROADMAP.md | All |

- **Stakeholders and product owners** should focus on the Master Specification and Development Roadmap.
- **Backend developers** should read all documents, with particular attention to Database Entities and Schema.
- **Frontend developers** should prioritise the Master Specification and Coding Standards.
- **Reviewers** must be familiar with all documents to evaluate compliance during code review.

---

## 6. Documentation Catalogue

The HHMS documentation suite consists of the following documents:

| Document ID | Document Name | Description |
|-------------|---------------|-------------|
| HHMS-DOC-001 | INDEX.md | Master index and documentation navigation guide |
| HHMS-DOC-002 | MASTER_SPECIFICATION.md | Complete system specification covering all features, modules, user roles, and business rules |
| HHMS-DOC-003 | DATABASE_ENTITIES.md | Definition of all database entities, their attributes, relationships, and business constraints |
| HHMS-DOC-004 | DATABASE_SCHEMA.md | Physical database schema including tables, columns, data types, indexes, and migrations |
| HHMS-DOC-005 | CODING_STANDARDS.md | Coding conventions, naming rules, file structure standards, and code quality expectations |
| HHMS-DOC-006 | DEVELOPMENT_ROADMAP.md | Project milestones, delivery timeline, and phased feature rollout plan |

This catalogue defines the documentation approved for the current project phase. Future documentation may be added through the project's document revision process.

---

## 7. Development Workflow

All HHMS development follows a strict sequential workflow. No step may be skipped or performed out of order.

```
Specification
    ↓
Review
    ↓
Implementation
    ↓
Code Review
    ↓
Testing
    ↓
Git Commit
    ↓
Next Milestone
```

### Workflow Stage Descriptions

**Specification**
The relevant documentation is written or updated to fully describe the feature, entity, or change. All requirements, constraints, and acceptance criteria are explicitly documented.

**Review**
The specification is reviewed by the team for completeness, accuracy, and feasibility. Any gaps or ambiguities are resolved before proceeding. Documentation must be approved before implementation begins.

**Implementation**
Code is written strictly according to the approved specification. Developers must follow the Coding Standards document at all times. No features beyond the specification may be introduced.

**Code Review**
All implementation is reviewed by at least one other team member. The review verifies compliance with the specification, coding standards, and architectural patterns. Issues must be resolved before proceeding.

**Testing**
The implementation is tested against the acceptance criteria defined in the specification. This includes unit tests, integration tests, and manual verification where appropriate. All tests must pass.

**Git Commit**
Approved and tested code is committed to the repository following the established commit conventions. The commit message must reference the relevant specification document and milestone.

**Next Milestone**
The completed work is incorporated into the project milestone. The Development Roadmap is updated to reflect progress, and the next milestone's specification phase begins.

---

## 8. Document Status Definitions

Every HHMS document carries a status indicator. The following statuses are used across all documentation:

| Status | Definition |
|--------|------------|
| **Draft** | Document is under initial creation. Content is incomplete and subject to significant change. Must not be used as a basis for implementation. |
| **Under Review** | Document is complete and awaiting team review. Content may change based on feedback. Must not be used as a basis for implementation until approved. |
| **Approved** | Document has passed review and is accepted as the current specification. Implementation may proceed based on this document. |
| **Active** | Document is the current, authoritative source. All implementation and decisions must align with this document. |
| **Deprecated** | Document has been superseded by a newer version or is no longer relevant. Must not be used for new work. Retained for historical reference only. |
| **Archived** | Document is preserved for audit and historical purposes. No longer applicable to the current project state. |

---

Document State: FROZEN
Approved For: Phase 1 Development

*End of Document — HHMS-DOC-001*
