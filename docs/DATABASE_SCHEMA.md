# HHMS Database Schema

---

## 1. Purpose

This document defines the physical database schema for the Homoeopathic Hospital Management System (HHMS). It translates the approved business entities into a normalized relational database structure for implementation.

This document specifies:

- Database tables
- Columns
- Data types
- Primary keys
- Foreign keys
- Constraints
- Indexes

This document shall not introduce new business entities or modify approved business rules. All schema definitions shall conform to the approved entity model documented in DATABASE_ENTITIES.md.

---

## 2. Database Design Principles

The HHMS database shall follow the following principles:

- Third Normal Form (3NF) shall be followed unless otherwise justified.
- Every table shall represent one approved business entity.
- Integer surrogate primary keys shall be used for all tables.
- Business identifiers shall remain separate from primary keys.
- Referential integrity shall be enforced using foreign keys.
- Historical records shall be preserved.
- Optional modules shall remain independent of one another.
- The database shall support offline-first operation.
- The schema shall remain simple, maintainable, and optimized for low-resource hardware.
- Database design shall remain independent of application framework and programming language.

---

## 3. Naming Conventions

The following naming conventions shall be used throughout the database.

### Tables

- Singular nouns.
- PascalCase.

Examples:

- Patient
- Visit
- Prescription
- MedicineBatch

### Columns

- snake_case.
- Lowercase.

Examples:

- patient_id
- visit_date
- created_at

### Primary Keys

Every table shall use:

id

### Foreign Keys

Foreign keys shall reference the parent table name followed by `_id`.

Examples:

- patient_id
- visit_id
- prescription_id

### Constraints

Constraint names shall use descriptive prefixes.

Examples:

- pk_patient
- fk_visit_patient
- uq_patient_number

### Indexes

Indexes shall use the prefix:

idx_

Example:

idx_patient_number

---

## 4. Table Overview

The following tables constitute the HHMS Version 1.0 database schema.

### Core Tables

| Table | Module | Purpose |
|--------|--------|---------|
| Patient | Core | Patient master records |
| Visit | Core | Patient encounters |
| OPDToken | Core | OPD queue management |
| Prescription | Core | Clinical prescriptions |
| User | Core | System users |
| Role | Core | User roles |
| AuditLog | Core | Audit trail |

### Pharmacy Module (Optional)

| Table | Purpose |
|--------|---------|
| Medicine | Medicine master |
| MedicineBatch | Medicine inventory batches |
| DispensingRecord | Dispensing history |

### Simple Stock Register (Optional)

| Table | Purpose |
|--------|---------|
| InventoryItem | General inventory items |
| StockTransaction | Inventory movement history |

### IPD Module (Optional)

| Table | Purpose |
|--------|---------|
| Admission | Patient admissions |
| Bed | Bed master |
| Discharge | Patient discharge records |

### Laboratory Module (Optional)

| Table | Purpose |
|--------|---------|
| Investigation | Investigation requests |
| InvestigationResult | Investigation outcomes |

### Billing Module (Optional)

| Table | Purpose |
|--------|---------|
| Invoice | Billing records |
| Payment | Payment transactions |

### Medical Records Module (Optional)

| Table | Purpose |
|--------|---------|
| MedicalDocument | Patient-associated documents |

---

