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

---

### Table: OPDToken

**Purpose**

Stores the outpatient consultation queue for Patient Visits. Each OPD Token represents a sequential queue number assigned to a Visit and tracks the patient's consultation status.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| visit_id | Integer | No | FK | References Visit |
| token_number | Integer | No | | Sequential token number |
| queue_date | Date | No | | Date of queue generation |
| queue_status | String(20) | No | | Waiting, Called, In Consultation, Completed, Cancelled |
| generated_at | DateTime | No | | Token generation timestamp |
| called_at | DateTime | Yes | | Time patient was called |
| completed_at | DateTime | Yes | | Consultation completion time |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- queue_date + token_number

---

#### Foreign Keys

- visit_id → Visit.id

---

#### Indexes

- visit_id
- queue_date
- token_number
- queue_status

---

#### Relationships

- One OPDToken → One Visit
- One Visit → One OPDToken

---

---

### Table: Prescription

**Purpose**

Stores the clinical prescription issued during a Patient Visit. Each Prescription records the diagnosis, clinical observations, treatment plan, and prescribing medical officer. Dispensed medicines are recorded separately in the Pharmacy module.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| visit_id | Integer | No | FK | References Visit |
| prescription_number | String(20) | No | Unique | Human-readable prescription identifier |
| diagnosis | Text | Yes | | Clinical diagnosis |
| clinical_notes | Text | Yes | | Examination findings and observations |
| treatment_plan | Text | Yes | | General treatment instructions |
| prescribed_by | Integer | No | FK | References User |
| prescription_datetime | DateTime | No | | Date and time of prescription |
| printed_at | DateTime | Yes | | First print timestamp |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- prescription_number

---

#### Foreign Keys

- visit_id → Visit.id
- prescribed_by → User.id

---

#### Indexes

- visit_id
- prescription_number
- prescribed_by
- prescription_datetime

---

#### Relationships

- One Prescription → One Visit
- One Visit → One Prescription
- One Prescription → Zero or More Dispensing Records
- Many Prescriptions → One User

---

---

### Table: User

**Purpose**

Stores authenticated system users authorized to access HHMS. The table maintains user identity, authentication information, account status, and operational metadata.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| username | String(50) | No | Unique | Unique login username |
| password_hash | String(255) | No | | Secure password hash |
| full_name | String(150) | No | | User's full name |
| email | String(150) | Yes | Unique | Email address |
| mobile_number | String(20) | Yes | | Contact number |
| designation | String(100) | Yes | | Professional designation |
| is_active | Boolean | No | | Account status |
| last_login | DateTime | Yes | | Last successful login |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- username
- email

---

#### Foreign Keys

None

---

#### Indexes

- username
- email
- is_active

---

#### Relationships

- One User → One or More Roles
- One User → Many Visits
- One User → Many Prescriptions
- One User → Many OPDTokens
- One User → Many AuditLog Entries
- One User → Many Admissions
- One User → Many Discharges
- One User → Many Investigation Results
- One User → Many Invoices
- One User → Many Payments

---

---

### Table: Role

**Purpose**

Stores the roles assigned to system users for role-based access control (RBAC). Roles define the functional responsibilities of users within HHMS.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| role_name | String(50) | No | Unique | Name of the role |
| description | Text | Yes | | Role description |
| is_active | Boolean | No | | Active status |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- role_name

---

#### Foreign Keys

None

---

#### Indexes

- role_name
- is_active

---

#### Relationships

- One Role → Many Users

---

---

### Table: AuditLog

**Purpose**

Stores a permanent record of significant system activities performed by authenticated users. The AuditLog table supports accountability, traceability, operational monitoring, and compliance requirements.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| user_id | Integer | No | FK | References User |
| activity | String(100) | No | | Activity performed |
| entity_name | String(100) | No | | Business entity affected |
| entity_id | Integer | Yes | | Identifier of the affected record |
| action_timestamp | DateTime | No | | Date and time of the activity |
| ip_address | String(45) | Yes | | Client IP address |
| remarks | Text | Yes | | Additional audit information |

---

#### Primary Key

- id

---

#### Unique Constraints

None

---

#### Foreign Keys

- user_id → User.id

---

#### Indexes

- user_id
- action_timestamp
- entity_name

---

#### Relationships

- Many AuditLog Entries → One User

---

---

### Table: Medicine

**Purpose**

Stores the master records of homoeopathic medicines available within the Pharmacy module. This table defines the identity of each medicine independent of potency, manufacturer, batch, or stock.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| medicine_code | String(30) | No | Unique | Unique medicine code |
| medicine_name | String(150) | No | | Medicine name |
| scientific_name | String(200) | Yes | | Scientific or botanical name |
| medicine_type | String(30) | No | | Mother Tincture, Dilution, Biochemic, etc. |
| description | Text | Yes | | Additional notes |
| is_active | Boolean | No | | Active status |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- medicine_code
- medicine_name

---

#### Foreign Keys

None

---

#### Indexes

- medicine_code
- medicine_name
- medicine_type

---

#### Relationships

- One Medicine → Many MedicineBatches
- One Medicine → Many DispensingRecords

---

---

### Table: MedicineBatch

**Purpose**

Stores inventory batches for each Medicine. Every batch represents a specific potency, manufacturer, batch number, expiry date, and available stock used for dispensing.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| medicine_id | Integer | No | FK | References Medicine |
| batch_number | String(50) | No | | Manufacturer batch number |
| potency | String(20) | No | | Q, X, C, LM etc. |
| manufacturer | String(150) | Yes | | Manufacturer name |
| manufacture_date | Date | Yes | | Manufacturing date |
| expiry_date | Date | Yes | | Expiry date |
| purchase_price | Decimal(10,2) | Yes | | Purchase price |
| selling_price | Decimal(10,2) | Yes | | Selling price |
| quantity_in_stock | Decimal(10,2) | No | | Current stock quantity |
| minimum_stock | Decimal(10,2) | Yes | | Minimum stock level |
| storage_location | String(100) | Yes | | Shelf or storage location |
| is_active | Boolean | No | | Active status |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- medicine_id + batch_number

---

#### Foreign Keys

- medicine_id → Medicine.id

---

#### Indexes

- medicine_id
- batch_number
- potency
- expiry_date

---

#### Relationships

- Many MedicineBatches → One Medicine
- One MedicineBatch → Many DispensingRecords

---

