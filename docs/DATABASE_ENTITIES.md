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