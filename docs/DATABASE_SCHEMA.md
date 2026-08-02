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

## 5. Core Tables

---

### Table: Patient

**Purpose**

Stores the permanent demographic and registration information of every patient receiving healthcare services within HHMS.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| patient_number | String(20) | No | Unique | Human-readable patient identifier |
| first_name | String(100) | No | | First name |
| middle_name | String(100) | Yes | | Middle name |
| last_name | String(100) | No | | Last name |
| gender | String(20) | No | | Gender |
| date_of_birth | Date | Yes | | Date of birth |
| age | Integer | Yes | | Age at registration if DOB unavailable |
| blood_group | String(5) | Yes | | Blood group |
| mobile_number | String(20) | Yes | | Primary contact number |
| email | String(150) | Yes | | Email address |
| address | Text | Yes | | Residential address |
| city | String(100) | Yes | | City |
| state | String(100) | Yes | | State |
| postal_code | String(20) | Yes | | Postal code |
| occupation | String(100) | Yes | | Occupation |
| marital_status | String(30) | Yes | | Marital status |
| registration_date | DateTime | No | | Registration date and time |
| is_active | Boolean | No | | Active patient flag |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- patient_number

---

#### Foreign Keys

None

---

#### Indexes

- patient_number
- first_name
- last_name
- mobile_number

---

#### Relationships

- One Patient → Many Visits
- One Patient → Many Admissions
- One Patient → Many Medical Documents

---

---

### Table: Visit

**Purpose**

Stores every clinical encounter between a Patient and the hospital. Each Visit represents a unique outpatient consultation or other clinical encounter and serves as the parent record for clinical activities performed during that encounter.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| patient_id | Integer | No | FK | References Patient |
| visit_number | String(20) | No | Unique | Human-readable visit identifier |
| visit_type | String(20) | No | | OPD, Follow-up, Emergency, etc. |
| visit_datetime | DateTime | No | | Date and time of visit |
| chief_complaint | Text | Yes | | Primary complaint |
| consultation_status | String(20) | No | | Waiting, In Progress, Completed, Cancelled |
| consulting_doctor_id | Integer | No | FK | References User |
| remarks | Text | Yes | | Administrative or clinical remarks |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- visit_number

---

#### Foreign Keys

- patient_id → Patient.id
- consulting_doctor_id → User.id

---

#### Indexes

- patient_id
- visit_number
- visit_datetime
- consulting_doctor_id

---

#### Relationships

- Many Visits → One Patient
- One Visit → One OPDToken
- One Visit → One Prescription
- One Visit → Zero or One Invoice
- One Visit → Zero or More Investigations

---

