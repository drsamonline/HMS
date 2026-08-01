# HHMS Database Entities

---

## 1. Purpose

This document defines the business entities used throughout the Homoeopathic Hospital Management System (HHMS). It serves as the authoritative reference for identifying the information managed by the system before physical database design begins.

Each entity represents a real-world object or concept within the hospital workflow. This document describes the purpose and relationships of each entity but does not define database tables, column types, indexes, or implementation details.

The entities defined in this document form the basis for the database schema, backend models, repositories, services, APIs, and user interface.

---

## 2. Entity Design Principles

The following principles apply to all entities:

- Each entity shall represent a single business concept.
- Each entity shall have a single primary responsibility.
- Duplicate storage of information shall be avoided.
- Relationships shall be explicitly defined.
- Optional modules shall own only their own entities.
- Mandatory modules shall remain independent of optional modules.
- Historical records shall be preserved.
- Entity definitions shall remain independent of implementation technology.

---

## 3. Entity Categories

HHMS entities are organised into the following categories:

### Core Entities

- Patient
- Visit
- OPD Token
- Prescription
- User
- Role
- Audit Log

### Optional Module Entities

**Pharmacy**

- Medicine
- Medicine Batch
- Dispensing Record

**Simple Stock Register**

- Stock Item
- Stock Transaction

**IPD**

- Admission
- Bed
- Discharge

**Laboratory**

- Investigation
- Investigation Result

**Billing**

- Invoice
- Payment

**Medical Records**

- Medical Document

---

## 4. Entity Documentation Standard

Each entity shall be documented using the following structure:

- Purpose
- Responsibilities
- Owned Information
- Relationships
- Business Rules
- Lifecycle
- Module Ownership

No implementation details shall be included in this document.

---

*End of Current Section*

---

---

# Entity: Patient

## Purpose

Represents an individual receiving healthcare services within HHMS. The Patient entity serves as the primary business entity and forms the foundation for all clinical, administrative, and operational records.

## Responsibilities

- Maintain a unique patient identity.
- Store patient demographic information.
- Support patient registration.
- Maintain continuity of care across multiple visits.
- Link all patient-related clinical and administrative records.

## Owned Information

- Patient identification.
- Demographic information.
- Contact information.
- Registration details.
- Patient status.

## Relationships

- One Patient may have many Visits.
- One Patient may have many Prescriptions.
- One Patient may have many OPD Tokens.
- One Patient may have zero or many Admissions.
- One Patient may have zero or many Laboratory Investigations.
- One Patient may have zero or many Billing Records.
- One Patient may have zero or many Medical Documents.

## Business Rules

- Every Patient shall have one unique patient identifier.
- A Patient may have multiple visits throughout their lifetime.
- Patient demographic information may be updated without affecting historical clinical records.
- A Patient cannot be permanently deleted once clinical records exist.

## Lifecycle

Register → Active → Update → Archive (if permitted by policy)

## Module Ownership

Core

---

# Entity: Visit

## Purpose

Represents a single clinical encounter between a registered Patient and the hospital. Every consultation, examination, treatment, or follow-up is recorded as an individual Visit.

## Responsibilities

- Record each patient encounter.
- Maintain chronological clinical history.
- Link consultations, prescriptions, investigations, and other clinical activities performed during the encounter.
- Distinguish multiple visits for the same patient.

## Relationships

- One Visit belongs to one Patient.
- One Visit may have one OPD Token.
- One Visit may have one or more Prescriptions.
- One Visit may have zero or more Laboratory Investigations.
- One Visit may have zero or one Billing Record.
- One Visit is recorded by one User.

## Business Rules

- Every Visit shall belong to exactly one Patient.
- A Patient may have multiple Visits.
- Clinical information shall be associated with the Visit in which it was recorded.
- Historical Visits shall remain available for future reference.

## Lifecycle

Create → Consultation → Complete → Historical Record

## Module Ownership

Core

---

# Entity: OPD Token

## Purpose

Represents the sequential queue token assigned to a Patient for a specific outpatient Visit. It supports efficient patient flow and consultation order within the Out-Patient Department.

## Responsibilities

- Assign a sequential consultation token.
- Maintain the consultation queue.
- Link the queue position to a specific Visit.
- Record the consultation status.

## Relationships

- One OPD Token belongs to one Visit.
- One Visit may have one OPD Token.
- One OPD Token is issued by one User.

## Business Rules

- Every OPD Token shall be associated with exactly one Visit.
- Token numbers shall be generated sequentially.
- Token numbers may restart according to the hospital's configured operational period.
- Completed and cancelled tokens shall remain available for historical reference.
- A Visit shall not have more than one active OPD Token.

## Lifecycle

Generate → Waiting → In Consultation → Completed / Cancelled

## Module Ownership

Core

---

# Entity: Prescription

## Purpose

Represents the clinical treatment plan issued during a Patient Visit. A Prescription records the medicines, dosage instructions, and clinical recommendations provided by the consulting medical officer.

## Responsibilities

- Record the prescribed treatment.
- Associate treatment with a specific Visit.
- Maintain prescription history.
- Support printing of prescriptions.
- Provide the dispensing reference for the Pharmacy module when enabled.

## Relationships

- One Prescription belongs to one Visit.
- One Visit may have one or more Prescriptions.
- One Prescription is created by one User.
- One Prescription may result in zero or more Dispensing Records when the Pharmacy module is enabled.

## Business Rules

- Every Prescription shall belong to exactly one Visit.
- A Visit may contain multiple Prescriptions when clinically required.
- Prescriptions shall remain permanently linked to their originating Visit.
- Printed prescriptions shall accurately represent the recorded prescription.
- Pharmacy dispensing shall not modify the original Prescription.

## Lifecycle

Create → Print → Dispense (Optional) → Historical Record

## Module Ownership

Core

---

# Entity: User

## Purpose

Represents an authenticated individual authorized to access HHMS for performing administrative, clinical, or operational activities according to assigned permissions.

## Responsibilities

- Access the system through authenticated login.
- Perform authorized clinical or administrative operations.
- Create, modify, and view records according to assigned permissions.
- Maintain accountability through recorded user activities.

## Relationships

- One User shall have one or more Roles.
- One User may register many Patients.
- One User may record many Visits.
- One User may create many Prescriptions.
- One User may issue many OPD Tokens.
- One User may generate many Audit Log entries.

## Business Rules

- Every User shall have at least one assigned Role.
- User accounts may be active or inactive.
- Only authenticated Users may access protected functions.
- All significant User activities shall be recorded in the Audit Log.
- Deactivating a User shall not affect historical records created by that User.

## Lifecycle

Create → Activate → Operate → Update → Deactivate

## Module Ownership

Core

---

# Entity: Role

## Purpose

Represents a collection of permissions assigned to Users to control access to modules and system functions.

## Responsibilities

- Define the responsibilities of a User.
- Control access to system modules.
- Control access to business functions.
- Support role-based access control throughout HHMS.

## Relationships

- One Role may be assigned to many Users.
- One User shall have one or more Roles.

## Business Rules

- Every Role shall have a unique name.
- A Role may be assigned to multiple Users.
- Every User shall have at least one assigned Role.
- Changes to a Role shall apply only to future access permissions and shall not modify historical records.

## Lifecycle

Create → Assign → Modify → Retire

## Module Ownership

Core

---

# Entity: Audit Log

## Purpose

Represents a permanent record of significant activities performed within HHMS. The Audit Log supports accountability, traceability, operational monitoring, and compliance requirements.

## Responsibilities

- Record significant system activities.
- Record the User responsible for each activity.
- Record the date and time of each activity.
- Preserve an auditable history of important events.

## Relationships

- One Audit Log entry is associated with one User.
- One User may generate many Audit Log entries.

## Business Rules

- Audit Log entries shall be created automatically for significant system activities.
- Existing Audit Log entries shall not be deleted through normal system operation.
- Audit Log records shall remain available for authorized review.
- Audit Log records shall preserve historical accountability even if related Users become inactive.

## Lifecycle

Create → Retain → Archive (if permitted by institutional policy)

## Module Ownership

Core

---

# Entity: Medicine

## Purpose

Represents a homoeopathic medicinal substance available for dispensing within the Pharmacy module. A Medicine defines the identity of the medicinal substance independent of potency, batch, or stock quantity.

## Responsibilities

- Maintain the identity of a homoeopathic medicine.
- Support prescribing and dispensing.
- Provide the parent record for potency-specific inventory.
- Support medicine search and reporting.

## Relationships

- One Medicine may have many Medicine Batches.
- One Medicine may appear in many Prescriptions.
- One Medicine may appear in many Dispensing Records.

## Business Rules

- Every Medicine shall represent a single homoeopathic medicinal substance.
- Potency shall not create a separate Medicine.
- Batch information shall be maintained separately.
- Stock quantity shall not be maintained within the Medicine entity.

## Lifecycle

Create → Active → Update → Retire

## Module Ownership

Pharmacy (Optional)

---

# Entity: Medicine Batch

## Purpose

Represents a specific inventory batch of a Medicine. A Medicine Batch identifies the potency, manufacturer, batch number, expiry, and available stock used for dispensing.

## Responsibilities

- Identify a specific inventory batch.
- Distinguish medicines by potency and batch.
- Support stock management.
- Support expiry tracking.
- Support dispensing operations.

## Relationships

- One Medicine Batch belongs to one Medicine.
- One Medicine may have many Medicine Batches.
- One Medicine Batch may appear in many Dispensing Records.

## Business Rules

- Every Medicine Batch shall belong to exactly one Medicine.
- Every Medicine Batch shall have one potency.
- Every Medicine Batch shall have one batch identifier.
- Stock shall be maintained at the Medicine Batch level.
- Expired Medicine Batches shall not be available for dispensing.
- Multiple Medicine Batches of the same Medicine and potency may exist simultaneously.

## Lifecycle

Receive → Available → Dispense → Exhausted / Expired

## Module Ownership

Pharmacy (Optional)

---

# Entity: Dispensing Record

## Purpose

Represents the dispensing of one or more Medicine Batches against a Prescription. It provides a permanent record of medicines issued to a Patient and supports inventory traceability.

## Responsibilities

- Record medicines dispensed for a Prescription.
- Link dispensing activities to the corresponding Patient Visit.
- Record the Medicine Batch used for dispensing.
- Support pharmacy history and reporting.

## Relationships

- One Dispensing Record belongs to one Prescription.
- One Dispensing Record may include one or more Medicine Batches.
- One Medicine Batch may appear in many Dispensing Records.
- One Dispensing Record is completed by one User.

## Business Rules

- Every Dispensing Record shall be associated with exactly one Prescription.
- Dispensing shall reference available Medicine Batches.
- Dispensing shall not modify the original Prescription.
- Every dispensing activity shall remain permanently recorded.
- Dispensing history shall remain available even if stock is exhausted.

## Lifecycle

Create → Complete → Historical Record

## Module Ownership

Pharmacy (Optional)