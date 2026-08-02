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
- One Visit may have one Prescription.
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
- One Visit may have one Prescription.
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

---

# Entity: Inventory Item

## Purpose

Represents a non-pharmacy item maintained within the Simple Stock Register. Inventory Items include general hospital supplies and consumables that are managed independently of Pharmacy inventory.

## Responsibilities

- Maintain the identity of a general inventory item.
- Support stock receipt and issue.
- Support inventory reporting.
- Provide the reference entity for stock transactions.

## Relationships

- One Inventory Item may have many Stock Transactions.

## Business Rules

- Every Inventory Item shall represent a single inventory article.
- Pharmacy medicines shall not be stored as Inventory Items.
- Current stock shall be derived from Stock Transactions.
- Inventory Items may be active or inactive.

## Lifecycle

Create → Active → Update → Retire

## Module Ownership

Simple Stock Register (Optional)

---

# Entity: Stock Transaction

## Purpose

Represents a single movement of an Inventory Item within the Simple Stock Register. It records every receipt, issue, adjustment, or return affecting inventory.

## Responsibilities

- Record inventory movements.
- Maintain stock movement history.
- Support current stock calculation.
- Support inventory reporting.
- Preserve complete transaction history.

## Relationships

- One Stock Transaction belongs to one Inventory Item.
- One Inventory Item may have many Stock Transactions.
- One Stock Transaction is recorded by one User.

## Business Rules

- Every Stock Transaction shall reference exactly one Inventory Item.
- Stock balance shall be derived from Stock Transactions.
- Stock Transactions shall remain permanently recorded.
- Historical Stock Transactions shall not be deleted through normal system operation.

## Lifecycle

Create → Record → Historical Record

## Module Ownership

Simple Stock Register (Optional)

---

# Entity: Admission

## Purpose

Represents the admission of a Patient for inpatient care. An Admission records the beginning of an inpatient episode and serves as the parent record for all IPD activities during that stay.

## Responsibilities

- Record patient admission.
- Link the admission to the Patient.
- Associate the admission with a Bed.
- Maintain the inpatient episode.
- Support discharge processing.

## Relationships

- One Admission belongs to one Patient.
- One Patient may have many Admissions.
- One Admission is assigned one Bed.
- One Admission has one Discharge.
- One Admission is recorded by one User.

## Business Rules

- Every Admission shall belong to exactly one Patient.
- A Patient may have multiple Admissions over time.
- An active Admission shall have one assigned Bed.
- An Admission shall remain permanently recorded after discharge.
- A Patient shall not have more than one active Admission at the same time.

## Lifecycle

Create → Admit → Active → Discharged → Historical Record

## Module Ownership

IPD (Optional)

---

# Entity: Bed

## Purpose

Represents a physical inpatient bed available for patient admission within the IPD module. A Bed is a hospital resource that may be allocated to different Admissions over time.

## Responsibilities

- Identify an inpatient bed.
- Support bed allocation.
- Record bed availability.
- Support inpatient occupancy management.

## Relationships

- One Bed may be assigned to many Admissions over time.
- One Admission shall be assigned one Bed.

## Business Rules

- Every Bed shall have a unique identity.
- A Bed may be occupied by only one active Admission at a time.
- A Bed may remain unoccupied.
- Bed allocation history shall be preserved.

## Lifecycle

Create → Available → Occupied → Available → Retired

## Module Ownership

IPD (Optional)

---

# Entity: Discharge

## Purpose

Represents the formal completion of an inpatient Admission. A Discharge records the conclusion of an inpatient episode and the release of the Patient from hospital care.

## Responsibilities

- Record completion of an Admission.
- Document discharge information.
- Release the allocated Bed.
- Complete the inpatient episode.
- Support discharge reporting.

## Relationships

- One Discharge belongs to one Admission.
- One Admission has one Discharge.
- One Discharge is completed by one User.

## Business Rules

- Every Discharge shall belong to exactly one Admission.
- An Admission shall have only one Discharge.
- A Patient cannot be discharged without an active Admission.
- Completing a Discharge shall release the associated Bed.
- Discharge records shall remain permanently available for historical reference.

## Lifecycle

Create → Complete → Historical Record

## Module Ownership

IPD (Optional)

---

# Entity: Investigation

## Purpose

Represents a laboratory investigation requested for a Patient during a Visit or Admission. It records the investigation request and tracks its progress until completion.

## Responsibilities

- Record investigation requests.
- Associate investigations with the relevant Patient encounter.
- Track investigation status.
- Support laboratory workflow.

## Relationships

- One Investigation belongs to one Patient.
- One Investigation belongs to one Visit or one Admission.
- One Investigation has one Investigation Result.
- One Investigation is requested by one User.

## Business Rules

- Every Investigation shall belong to exactly one Patient.
- Every Investigation shall be associated with one clinical encounter.
- An Investigation may exist before a result is available.
- An Investigation shall have only one final Investigation Result.
- Cancelled Investigations shall remain in the historical record.

## Lifecycle

Request → Pending → In Progress → Completed / Cancelled

## Module Ownership

Laboratory (Optional)

---

# Entity: Investigation Result

## Purpose

Represents the recorded outcome of a Laboratory Investigation. It documents the findings produced for an Investigation and forms part of the Patient's permanent clinical record.

## Responsibilities

- Record the outcome of an Investigation.
- Associate results with the corresponding Investigation.
- Support review and printing of laboratory reports.
- Preserve the clinical history of laboratory findings.

## Relationships

- One Investigation Result belongs to one Investigation.
- One Investigation has one Investigation Result.
- One Investigation Result is recorded by one User.

## Business Rules

- Every Investigation Result shall belong to exactly one Investigation.
- An Investigation shall have only one final Investigation Result.
- Investigation Results shall remain permanently linked to their originating Investigation.
- Investigation Results shall remain available for historical reference.
- Completed Investigation Results shall support report generation and printing.

## Lifecycle

Create → Verify → Complete → Historical Record

## Module Ownership

Laboratory (Optional)

---

# Entity: Invoice

## Purpose

Represents the financial charges generated for healthcare services provided to a Patient. An Invoice serves as the official billing document for a clinical encounter and forms the basis for payment collection.

## Responsibilities

- Record billable services.
- Calculate the total amount payable.
- Associate charges with the corresponding Patient encounter.
- Support invoice printing.
- Provide the basis for payment recording.

## Relationships

- One Invoice belongs to one Patient.
- One Invoice belongs to one Visit or one Admission.
- One Invoice may have one or more Payments.
- One Invoice is generated by one User.

## Business Rules

- Every Invoice shall belong to exactly one Patient.
- Every Invoice shall be associated with one clinical encounter.
- An Invoice may exist before any Payment is recorded.
- An Invoice shall remain permanently available for financial and audit purposes.
- Cancelling an Invoice shall not remove its historical record.

## Lifecycle

Create → Issue → Paid / Cancelled → Historical Record

## Module Ownership

Billing (Optional)

---

# Entity: Payment

## Purpose

Represents a financial transaction received against an Invoice. A Payment records the settlement of all or part of an Invoice and provides a permanent financial record.

## Responsibilities

- Record payments received.
- Associate payments with an Invoice.
- Support payment receipt generation.
- Maintain payment history.
- Support financial reporting.

## Relationships

- One Payment belongs to one Invoice.
- One Invoice may have one or more Payments.
- One Payment is recorded by one User.

## Business Rules

- Every Payment shall belong to exactly one Invoice.
- Multiple Payments may be recorded against a single Invoice.
- The total recorded Payments shall not exceed the Invoice amount.
- Payment records shall not modify the original Invoice.
- Payment records shall remain permanently available for financial and audit purposes.

## Lifecycle

Record → Confirm → Historical Record

## Module Ownership

Billing (Optional)

---

# Entity: Medical Document

## Purpose

Represents a clinical or administrative document permanently associated with a Patient's medical record. Medical Documents provide long-term storage and retrieval of patient-related documents generated within or attached to HHMS.

## Responsibilities

- Maintain patient-associated documents.
- Support document retrieval.
- Preserve historical clinical documentation.
- Support document printing where applicable.

## Relationships

- One Medical Document belongs to one Patient.
- One Patient may have many Medical Documents.
- One Medical Document may be associated with one Visit or one Admission.
- One Medical Document is created or recorded by one User.

## Business Rules

- Every Medical Document shall belong to exactly one Patient.
- Medical Documents shall remain permanently linked to the Patient record.
- Medical Documents shall support historical retrieval.
- Deleting a Patient shall not be permitted while Medical Documents exist.
- Medical Documents shall remain available according to institutional record-retention policies.

## Lifecycle

Create → Store → Retrieve → Archive (if permitted by institutional policy)

## Module Ownership

Medical Records (Optional)

