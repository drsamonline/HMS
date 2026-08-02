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

---

### Table: DispensingRecord

**Purpose**

Stores the dispensing of a specific MedicineBatch against a Prescription. Each record represents one medicine item dispensed by the pharmacy and provides complete inventory traceability.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| prescription_id | Integer | No | FK | References Prescription |
| medicine_batch_id | Integer | No | FK | References MedicineBatch |
| quantity_dispensed | Decimal(10,2) | No | | Quantity dispensed |
| dispensing_datetime | DateTime | No | | Date and time of dispensing |
| dispensed_by | Integer | No | FK | References User |
| remarks | Text | Yes | | Dispensing remarks |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

None

---

#### Foreign Keys

- prescription_id → Prescription.id
- medicine_batch_id → MedicineBatch.id
- dispensed_by → User.id

---

#### Indexes

- prescription_id
- medicine_batch_id
- dispensing_datetime
- dispensed_by

---

#### Relationships

- Many DispensingRecords → One Prescription
- Many DispensingRecords → One MedicineBatch
- Many DispensingRecords → One User

---

---

### Table: InventoryItem

**Purpose**

Stores the master records of non-pharmacy inventory items maintained by the Simple Stock Register module. This table defines the identity of general inventory items independent of stock movements.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| item_code | String(30) | No | Unique | Unique inventory item code |
| item_name | String(150) | No | | Inventory item name |
| category | String(100) | Yes | | Item category |
| unit | String(30) | No | | Unit of measurement |
| description | Text | Yes | | Additional description |
| minimum_stock | Decimal(10,2) | Yes | | Minimum stock level |
| is_active | Boolean | No | | Active status |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- item_code
- item_name

---

#### Foreign Keys

None

---

#### Indexes

- item_code
- item_name
- category

---

#### Relationships

- One InventoryItem → Many StockTransactions

---

---

### Table: StockTransaction

**Purpose**

Stores every movement of an InventoryItem within the Simple Stock Register. Each transaction records the receipt, issue, adjustment, or return of inventory and forms the basis for stock calculations and inventory history.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| inventory_item_id | Integer | No | FK | References InventoryItem |
| transaction_type | String(20) | No | | Receipt, Issue, Adjustment, Return |
| quantity | Decimal(10,2) | No | | Quantity moved |
| transaction_datetime | DateTime | No | | Date and time of transaction |
| reference_number | String(50) | Yes | | External reference document |
| recorded_by | Integer | No | FK | References User |
| remarks | Text | Yes | | Transaction remarks |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

None

---

#### Foreign Keys

- inventory_item_id → InventoryItem.id
- recorded_by → User.id

---

#### Indexes

- inventory_item_id
- transaction_type
- transaction_datetime
- recorded_by

---

#### Relationships

- Many StockTransactions → One InventoryItem
- Many StockTransactions → One User

---

---

### Table: Admission

**Purpose**

Stores inpatient admissions for Patients. Each Admission represents a single inpatient episode, including admission details, assigned bed, admitting user, and current admission status.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| patient_id | Integer | No | FK | References Patient |
| admission_number | String(20) | No | Unique | Human-readable admission identifier |
| admission_datetime | DateTime | No | | Date and time of admission |
| bed_id | Integer | No | FK | References Bed |
| admitted_by | Integer | No | FK | References User |
| admission_reason | Text | Yes | | Reason for admission |
| admission_status | String(20) | No | | Active, Discharged, Cancelled |
| remarks | Text | Yes | | Additional notes |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- admission_number

---

#### Foreign Keys

- patient_id → Patient.id
- bed_id → Bed.id
- admitted_by → User.id

---

#### Indexes

- patient_id
- admission_number
- admission_datetime
- admission_status
- bed_id

---

#### Relationships

- Many Admissions → One Patient
- Many Admissions → One Bed
- Many Admissions → One User
- One Admission → One Discharge

---

---

### Table: Bed

**Purpose**

Stores the master records of inpatient beds available within the hospital. The table defines each bed as a physical hospital resource that can be allocated to Admissions over time.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| bed_number | String(20) | No | Unique | Unique bed identifier |
| ward | String(100) | Yes | | Ward or department |
| room_number | String(50) | Yes | | Room number |
| bed_type | String(50) | Yes | | General, Private, ICU, etc. |
| occupancy_status | String(20) | No | | Available, Occupied, Maintenance |
| is_active | Boolean | No | | Active status |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- bed_number

---

#### Foreign Keys

None

---

#### Indexes

- bed_number
- ward
- room_number
- occupancy_status

---

#### Relationships

- One Bed → Many Admissions

---

---

### Table: Discharge

**Purpose**

Stores the discharge details for an inpatient Admission. Each Discharge records the completion of an inpatient episode and preserves the discharge information for clinical, administrative, and reporting purposes.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| admission_id | Integer | No | FK | References Admission |
| discharge_number | String(20) | No | Unique | Human-readable discharge identifier |
| discharge_datetime | DateTime | No | | Date and time of discharge |
| discharge_summary | Text | Yes | | Clinical discharge summary |
| discharge_status | String(20) | No | | Normal, Referred, LAMA, Death, Transfer |
| discharged_by | Integer | No | FK | References User |
| remarks | Text | Yes | | Additional notes |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- discharge_number
- admission_id

---

#### Foreign Keys

- admission_id → Admission.id
- discharged_by → User.id

---

#### Indexes

- admission_id
- discharge_number
- discharge_datetime
- discharged_by

---

#### Relationships

- One Discharge → One Admission
- Many Discharges → One User

---

---

### Table: Investigation

**Purpose**

Stores laboratory investigation requests generated during a Patient Visit or Admission. Each Investigation represents a single requested laboratory test and tracks its status until completion.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| patient_id | Integer | No | FK | References Patient |
| visit_id | Integer | Yes | FK | References Visit |
| admission_id | Integer | Yes | FK | References Admission |
| investigation_number | String(20) | No | Unique | Human-readable investigation identifier |
| investigation_name | String(150) | No | | Requested investigation |
| requested_by | Integer | No | FK | References User |
| requested_datetime | DateTime | No | | Date and time of request |
| investigation_status | String(20) | No | | Pending, In Progress, Completed, Cancelled |
| remarks | Text | Yes | | Additional notes |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- investigation_number

---

#### Foreign Keys

- patient_id → Patient.id
- visit_id → Visit.id
- admission_id → Admission.id
- requested_by → User.id

---

#### Indexes

- patient_id
- visit_id
- admission_id
- investigation_number
- investigation_status

---

#### Relationships

- Many Investigations → One Patient
- Many Investigations → One Visit (optional)
- Many Investigations → One Admission (optional)
- Many Investigations → One User
- One Investigation → Zero or One InvestigationResult

---

---

### Table: InvestigationResult

**Purpose**

Stores the final results of laboratory investigations. Each InvestigationResult records the outcome of a single Investigation and becomes part of the Patient's permanent medical record.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| investigation_id | Integer | No | FK | References Investigation |
| result_text | Text | Yes | | Laboratory findings |
| interpretation | Text | Yes | | Clinical interpretation |
| result_datetime | DateTime | No | | Date and time result was recorded |
| verified_by | Integer | Yes | FK | References User |
| verification_datetime | DateTime | Yes | | Date and time of verification |
| report_status | String(20) | No | | Draft, Verified, Released |
| remarks | Text | Yes | | Additional comments |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- investigation_id

---

#### Foreign Keys

- investigation_id → Investigation.id
- verified_by → User.id

---

#### Indexes

- investigation_id
- result_datetime
- report_status
- verified_by

---

#### Relationships

- One InvestigationResult → One Investigation
- Many InvestigationResults → One User (Verifier)

---

---

### Table: Invoice

**Purpose**

Stores billing records generated for healthcare services provided during a Patient Visit or Admission. Each Invoice represents a financial document used for payment collection and financial reporting.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| patient_id | Integer | No | FK | References Patient |
| visit_id | Integer | Yes | FK | References Visit |
| admission_id | Integer | Yes | FK | References Admission |
| invoice_number | String(20) | No | Unique | Human-readable invoice number |
| invoice_date | DateTime | No | | Date and time of invoice generation |
| total_amount | Decimal(10,2) | No | | Total invoice amount |
| payment_status | String(20) | No | | Pending, Partial, Paid, Cancelled |
| generated_by | Integer | No | FK | References User |
| remarks | Text | Yes | | Additional billing remarks |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- invoice_number

---

#### Foreign Keys

- patient_id → Patient.id
- visit_id → Visit.id
- admission_id → Admission.id
- generated_by → User.id

---

#### Indexes

- patient_id
- invoice_number
- invoice_date
- payment_status
- generated_by

---

#### Relationships

- Many Invoices → One Patient
- Many Invoices → One Visit (optional)
- Many Invoices → One Admission (optional)
- Many Invoices → One User
- One Invoice → One or More Payments

---

---

### Table: Payment

**Purpose**

Stores payments received against Invoices. Each Payment represents a single financial transaction and maintains the financial settlement history for billing and audit purposes.

---

#### Columns

| Column | Data Type | Null | Key | Description |
|---------|-----------|------|-----|-------------|
| id | Integer | No | PK | Internal primary key |
| invoice_id | Integer | No | FK | References Invoice |
| receipt_number | String(20) | No | Unique | Human-readable receipt number |
| payment_datetime | DateTime | No | | Date and time of payment |
| payment_method | String(30) | No | | Cash, Card, UPI, Bank Transfer, etc. |
| amount_paid | Decimal(10,2) | No | | Amount received |
| received_by | Integer | No | FK | References User |
| transaction_reference | String(100) | Yes | | External payment reference |
| remarks | Text | Yes | | Additional payment remarks |
| created_at | DateTime | No | | Record creation timestamp |
| updated_at | DateTime | No | | Last modification timestamp |

---

#### Primary Key

- id

---

#### Unique Constraints

- receipt_number

---

#### Foreign Keys

- invoice_id → Invoice.id
- received_by → User.id

---

#### Indexes

- invoice_id
- receipt_number
- payment_datetime
- payment_method
- received_by

---

#### Relationships

- Many Payments → One Invoice
- Many Payments → One User

---

