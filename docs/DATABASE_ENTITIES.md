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

