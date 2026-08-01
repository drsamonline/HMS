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

# Entity: User

## Purpose

Represents an authenticated individual authorized to access HHMS. A User is responsible for performing administrative, clinical, or operational activities within the system according to assigned roles.

## Responsibilities

- Authenticate into the system.
- Perform authorized operations.
- Create and modify business records.
- Generate printable documents where permitted.
- Maintain accountability through audit logging.

## Owned Information

- User identity.
- Login credentials.
- Account status.
- Assigned role(s).
- Authentication preferences.

## Relationships

- One User may have one or more Roles.
- One User may create many Visits.
- One User may create many Prescriptions.
- One User may perform many Audit Log entries.

## Business Rules

- Every User shall have at least one assigned Role.
- User accounts may be active or inactive.
- Authentication is mandatory before accessing protected functions.
- All significant actions performed by a User shall be recorded in the Audit Log.

## Lifecycle

Create → Activate → Operate → Update → Deactivate

## Module Ownership

Core

