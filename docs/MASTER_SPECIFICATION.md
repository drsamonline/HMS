# HHMS Master Specification

---

## 1. Document Information

This section contains the document metadata including title, document identifier, version number, current status, author, and date of last revision.

| Field | Value |
|-------|-------|
| **Title** | HHMS Master Specification |
| **Document ID** | HHMS-DOC-002 |
| **Version** | 1.0.0 |
| **Status** | Draft |
| **Author** | Dr. Sohil Momin |
| **Date** | 31 July 2026 |

---

## 2. Purpose

This document is the primary functional specification for the Homoeopathic Hospital Management System (HHMS). It defines the functional, operational, and compliance requirements that govern the development of the system.

The purpose of this document is to:

- Define the complete scope of HHMS.
- Document the expected behaviour of every module.
- Establish business rules and user workflows.
- Provide a single reference for development, testing, and validation.
- Support NABH AYUSH requirements.
- Support future ABDM/FHIR-compatible data exchange.
- Ensure consistent implementation throughout the project.

This document specifies **what the system must do**. It does not describe how the system will be implemented.

---

## 3. Scope

The Homoeopathic Hospital Management System (HHMS) is designed as a modular, offline-first hospital information system for homoeopathic hospitals, teaching institutions, clinics, and charitable healthcare centres.

### In Scope

- Patient registration and demographic management.
- OPD management with a high-throughput token queue.
- Homoeopathic prescription management.
- Optional Pharmacy module.
- Optional Simple Stock Register.
- Optional IPD module.
- Optional Laboratory module.
- Optional Billing module.
- Optional MRD module.
- User authentication and role-based access control.
- NABH AYUSH compliant record management.
- Print-first workflows for prescriptions, receipts, certificates, and reports.
- Feature-flag based module enabling and disabling without affecting existing data.
- Local data storage with future support for ABDM/FHIR-compatible data export.

### Out of Scope

The following are intentionally excluded from Version 1.0:

- AI diagnosis or clinical decision support.
- Built-in repertory or Materia Medica.
- Online appointment booking.
- Telemedicine.
- Cloud-only operation.
- Multi-hospital management.
- Accounting and payroll.
- HR management.
- Biomedical equipment management.
- CMS or website management.
- Third-party ERP integration.

The scope defined in this document is fixed for Version 1.0. New functionality shall only be introduced after formal approval and inclusion in a future project milestone.

---

## 4. Project Objectives

The Homoeopathic Hospital Management System (HHMS) shall achieve the following objectives:

### Primary Objectives

- Provide a simple, reliable, and efficient Hospital Management System for homoeopathic healthcare institutions.
- Minimize manual paperwork through structured digital record management.
- Support fast patient registration and high-volume OPD workflow.
- Maintain complete and accurate patient medical records.
- Improve prescription documentation and retrieval.
- Support NABH AYUSH documentation and operational requirements.
- Operate efficiently on low-resource computers without requiring continuous internet connectivity.
- Deliver a print-first workflow for all essential hospital documents.

### Technical Objectives

- Maintain a modular architecture where optional modules can be enabled or disabled independently.
- Preserve historical data even when modules are disabled.
- Ensure fast system startup and responsive operation on modest hardware.
- Provide secure role-based user access.
- Generate consistent and printable records across all modules.
- Support future ABDM/FHIR-compatible data export without changing core workflows.

### Project Objectives

- Follow a documentation-first development methodology.
- Maintain a clean, modular, and maintainable codebase.
- Prevent feature creep by implementing only approved requirements.
- Build the system incrementally through small, independently testable milestones.
- Deliver a stable and practical Version 1.0 suitable for real-world hospital use.

---

## 5. System Overview

The Homoeopathic Hospital Management System (HHMS) is an offline-first, print-first Hospital Management System designed specifically for homoeopathic hospitals, teaching institutions, clinics, and charitable healthcare centres.

The system is designed to simplify daily hospital operations by providing a modular platform that manages patient registration, outpatient services, prescriptions, pharmacy operations, inventory, billing, laboratory records, medical records, and reporting through independent functional modules.

HHMS follows a feature-flag architecture in which optional modules can be enabled or disabled according to institutional requirements. Disabling a module removes it completely from the user interface and workflow while preserving all historical data associated with that module.

The system is optimized for low-resource hardware and prioritizes reliability, speed, and ease of use over unnecessary complexity. All core operations are designed to function without continuous internet connectivity, making the system suitable for hospitals with limited infrastructure.

HHMS supports role-based access control, comprehensive audit logging, and standardized printable documents to meet operational and NABH AYUSH documentation requirements. The system is also designed to support future ABDM/FHIR-compatible data exchange without requiring major architectural changes.

### Core Characteristics

- Offline-first operation.
- Print-first workflow.
- Modular architecture with optional feature-based modules.
- Low-resource hardware compatibility.
- Homoeopathy-specific clinical workflow.
- NABH AYUSH documentation support.
- Future-ready ABDM/FHIR-compatible data export.
- Role-based security and audit logging.
- Scalable through modular expansion without affecting existing workflows.

---

## 6. Users and Roles

HHMS uses Role-Based Access Control (RBAC). Each user is assigned one or more roles that determine the modules, functions, and data they can access.

### 6.1 Administrator

**Responsibilities**

- Configure system settings.
- Manage users and roles.
- Enable or disable optional modules.
- View audit logs.
- Perform database backup and restore.
- Access all system modules.

---

### 6.2 Registration Desk

**Responsibilities**

- Register new patients.
- Search and update patient demographic information.
- Generate OPD tokens.
- Print patient registration receipts.
- Schedule or manage patient visits where applicable.

---

### 6.3 Medical Officer / Consultant

**Responsibilities**

- View patient records.
- Record clinical findings.
- Create and modify prescriptions.
- Request investigations.
- Access previous consultation history.
- Print prescriptions and certificates.

---

### 6.4 Pharmacist

*(Available only when the Pharmacy module is enabled.)*

**Responsibilities**

- Dispense prescribed medicines.
- Manage pharmacy inventory.
- Record batch numbers and expiry dates.
- Maintain homoeopathic medicine stock.
- Generate pharmacy-related reports.

---

### 6.5 Laboratory Staff

*(Available only when the Laboratory module is enabled.)*

**Responsibilities**

- Receive investigation requests.
- Record laboratory results.
- Print investigation reports.

---

### 6.6 Billing Staff

*(Available only when the Billing module is enabled.)*

**Responsibilities**

- Generate invoices.
- Record payments.
- Print receipts.
- View billing reports.

---

### 6.7 Medical Records Department (MRD)

*(Available only when the MRD module is enabled.)*

**Responsibilities**

- Maintain medical records.
- Archive patient documents.
- Retrieve historical records.
- Generate statutory reports.

---

### 6.8 Store Keeper

*(Available only when the Simple Stock Register module is enabled.)*

**Responsibilities**

- Record stock receipts.
- Record stock issues.
- Monitor stock levels.
- Generate stock reports.

---

### 6.9 System Principles

- Users may have multiple roles.
- Permissions shall be granted according to assigned roles.
- Unauthorized functions shall not be visible.
- Every significant user action shall be recorded in the audit log.
- Disabling a module shall automatically remove all related permissions while preserving historical data.

---

## 7. Functional Modules

HHMS is built as a modular system consisting of one mandatory core module and multiple optional modules. Optional modules can be enabled or disabled through system settings without affecting the operation of other modules or deleting historical data.

### 7.1 Core Modules

The following modules are mandatory and always available:

#### Patient Registration

- Register new patients.
- Search and retrieve patient records.
- Update demographic information.
- Generate patient identifiers.
- Maintain patient visit history.

#### OPD Management

- Generate sequential OPD tokens.
- Maintain consultation queue.
- Record outpatient consultations.
- Manage follow-up visits.
- Print OPD slips and consultation records.

#### Prescription Management

- Create homoeopathic prescriptions.
- Record diagnosis and clinical notes.
- Maintain prescription history.
- Print prescriptions.

#### User & Security Management

- User authentication.
- Role-based access control.
- Password management.
- Audit logging.
- Session management.

#### Reporting

- Daily OPD reports.
- Patient statistics.
- Module-specific reports.
- Printable summaries.

---

### 7.2 Optional Modules

The following modules may be enabled or disabled independently.

#### Pharmacy

- Medicine dispensing.
- Batch management.
- Mother tincture management.
- Potency management (X, C, LM/Q).
- Expiry tracking.
- Pharmacy reports.

#### Simple Stock Register

- General stock register.
- Stock receipt.
- Stock issue.
- Stock balance.
- Stock reports.

This module is independent of Pharmacy inventory.

#### IPD

- Admission.
- Bed allocation.
- Daily case records.
- Discharge summary.

#### Laboratory

- Investigation requests.
- Investigation results.
- Report printing.

#### Billing

- Invoice generation.
- Payment recording.
- Receipt printing.
- Billing reports.

#### Medical Records (MRD)

- Medical record management.
- Document archive.
- Record retrieval.

---

### 7.3 Module Independence

Each module shall:

- Operate independently.
- Communicate through defined interfaces.
- Store only its own data.
- Continue functioning regardless of the status of optional modules.

Disabling a module shall:

- Remove all related menus.
- Remove related workflows.
- Remove related permissions.
- Preserve all historical records.
- Not affect any other module.

---

## 8. Functional Requirements

The following functional requirements define the minimum capabilities required for Version 1.0 of HHMS. These requirements apply only to approved modules within the defined project scope.

### 8.1 General Requirements

- The system shall authenticate users before granting access.
- The system shall enforce role-based access permissions.
- The system shall record significant user activities in an audit log.
- The system shall support bilingual data presentation where configured.
- The system shall generate printable documents in a consistent format.
- The system shall preserve historical records during normal operation and module configuration changes.

---

### 8.2 Patient Registration

The system shall:

- Register new patients.
- Generate a unique patient identifier.
- Store demographic information.
- Search existing patients using multiple search criteria.
- Update patient information while preserving visit history.
- Display previous visit history.

---

### 8.3 OPD Management

The system shall:

- Generate sequential OPD tokens.
- Maintain a consultation queue.
- Register outpatient visits.
- Record consultation details.
- Support follow-up visits.
- Print OPD slips.

---

### 8.4 Prescription Management

The system shall:

- Create homoeopathic prescriptions.
- Record diagnosis and clinical findings.
- Record prescribed medicines and potencies.
- Maintain prescription history.
- Print prescriptions.

---

### 8.5 Pharmacy Module (Optional)

When enabled, the system shall:

- Dispense medicines.
- Maintain medicine inventory.
- Record batch numbers.
- Record expiry dates.
- Support Mother Tinctures.
- Support Decimal (X/D), Centesimal (C), and LM/Q potencies.
- Generate pharmacy reports.

---

### 8.6 Simple Stock Register (Optional)

When enabled, the system shall:

- Record stock receipt.
- Record stock issue.
- Display current stock balance.
- Generate stock reports.

This module shall remain independent of Pharmacy inventory.

---

### 8.7 IPD Module (Optional)

When enabled, the system shall:

- Register admissions.
- Allocate beds.
- Maintain inpatient records.
- Record discharge details.

---

### 8.8 Laboratory Module (Optional)

When enabled, the system shall:

- Record investigation requests.
- Record investigation results.
- Print laboratory reports.

---

### 8.9 Billing Module (Optional)

When enabled, the system shall:

- Generate invoices.
- Record payments.
- Print receipts.
- Generate billing reports.

---

### 8.10 Medical Records Module (Optional)

When enabled, the system shall:

- Archive patient records.
- Retrieve historical records.
- Maintain document references.

---

### 8.11 Reporting

The system shall:

- Generate daily operational reports.
- Generate module-specific reports.
- Support printing of all reports.

---

### 8.12 Module Behaviour

- Mandatory modules shall always remain available.
- Optional modules shall be independently enabled or disabled.
- Disabled modules shall not appear in the user interface.
- Disabling a module shall not delete historical data.
- Enabling a module shall restore access to existing data.


---

## 9. Non-Functional Requirements

The following non-functional requirements apply to the entire HHMS system.

### Performance

- The system shall provide responsive operation during normal hospital workflows.
- Patient registration and OPD token generation shall complete without unnecessary delay.
- The system shall remain usable on low-resource hardware.

### Availability

- The system shall operate without continuous internet connectivity.
- All core functionality shall remain available during offline operation.

### Reliability

- The system shall preserve data integrity during normal operation.
- Historical records shall not be lost when optional modules are disabled.
- The system shall support regular database backup and restoration.

### Security

- Access shall be controlled through authenticated user accounts.
- Permissions shall be enforced using role-based access control.
- User activities shall be recorded in the audit log.

### Usability

- The interface shall remain simple and consistent across all modules.
- Frequently used operations shall require the minimum practical number of steps.
- All major documents shall be printable.

### Compatibility

- The system shall support bilingual output where configured.
- The system shall support future ABDM/FHIR-compatible data export.
- The system shall function consistently regardless of which optional modules are enabled.

### Maintainability

- Modules shall remain independently maintainable.
- Changes to one module shall not require modification of unrelated modules.
- New approved modules shall integrate without affecting existing workflows.
---

## 10. Assumptions and Constraints

### Assumptions

The following assumptions apply to Version 1.0 of HHMS:

- The system will be deployed primarily in homoeopathic hospitals, teaching institutions, clinics, and charitable healthcare centres.
- Users will receive basic training before using the system.
- Each installation will operate independently unless future integration is implemented.
- Patient data entered into the system is the responsibility of authorized users.
- Hospital workflows follow standard clinical and administrative practices.

### Constraints

The following constraints govern the design and implementation of HHMS:

- The system shall follow a documentation-first development methodology.
- Version 1.0 shall implement only approved features defined in this specification.
- The system shall be optimized for low-resource hardware.
- The system shall support offline-first operation.
- The system shall follow a print-first workflow for all major hospital documents.
- Optional modules shall remain completely independent and may be enabled or disabled without affecting other modules.
- Disabling a module shall preserve all historical data.
- The system shall support NABH AYUSH operational requirements.
- The system architecture shall allow future ABDM/FHIR-compatible data export without requiring redesign of the core system.
- All implementation decisions shall comply with the approved project documentation.

---

## 11. Acceptance Criteria

HHMS Version 1.0 shall be considered complete when all of the following acceptance criteria are satisfied.

### Functional Acceptance

- All mandatory modules are fully operational.
- Each optional module can be independently enabled or disabled.
- Disabled modules remain completely hidden from the user interface.
- Historical data remains available after a module is re-enabled.
- Patient registration functions correctly.
- OPD token generation functions correctly.
- Prescription management functions correctly.
- All approved reports can be generated and printed.

### Operational Acceptance

- The system operates correctly without continuous internet connectivity.
- User authentication and role-based permissions function correctly.
- Audit logging records significant user activities.
- Backup and restoration procedures complete successfully.

### Compliance Acceptance

- Required NABH AYUSH documentation can be generated.
- Homoeopathic pharmacy workflows support Mother Tinctures, Decimal (X/D), Centesimal (C), and LM/Q potencies where the Pharmacy module is enabled.
- Bilingual printing functions correctly where configured.

### Quality Acceptance

- All approved functional requirements have been implemented.
- All approved non-functional requirements have been satisfied.
- No unapproved features have been introduced.
- The application is stable under normal operational use.
- All project documentation is complete and approved.

HHMS Version 1.0 shall be accepted only after all applicable acceptance criteria have been successfully verified.

---

## 12. Glossary

| Term | Definition |
|------|------------|
| **ABDM** | Ayushman Bharat Digital Mission. |
| **Audit Log** | A chronological record of significant user activities performed within the system. |
| **Batch** | A group of medicines manufactured or procured together and identified by a common batch number. |
| **Bilingual Output** | Display or printing of information in English and one configurable local language. |
| **Consultation** | A clinical encounter between a patient and a medical officer. |
| **Feature Flag** | A configuration setting used to enable or disable an optional module without affecting other modules or historical data. |
| **FHIR** | Fast Healthcare Interoperability Resources, a standard for exchanging healthcare information electronically. |
| **HHMS** | Homoeopathic Hospital Management System. |
| **IPD** | In-Patient Department. |
| **LM/Q Potency** | Fifty Millesimal homoeopathic potency scale. |
| **Medical Record** | The complete clinical and administrative record maintained for a patient. |
| **Mother Tincture** | A homoeopathic medicine prepared directly from the original source material before potentisation. |
| **MRD** | Medical Records Department. |
| **NABH AYUSH** | National Accreditation Board for Hospitals and Healthcare Providers standards applicable to AYUSH healthcare organizations. |
| **OPD** | Out-Patient Department. |
| **Patient Identifier** | A unique identifier assigned to each registered patient. |
| **Potency** | The strength of a homoeopathic medicine, including Decimal (X/D), Centesimal (C), and LM/Q scales. |
| **Prescription** | A documented treatment plan issued by a registered medical practitioner. |
| **Role-Based Access Control (RBAC)** | A security model in which user permissions are assigned according to predefined roles. |
| **Simple Stock Register** | An optional inventory module used to record general stock independent of pharmacy inventory. |
| **Token** | A sequential number assigned to a patient for OPD consultation queue management. |
| **Visit** | A single patient encounter recorded within the system. |
---

## 13. References

This section lists all external documents, standards, regulations, and resources referenced within this specification. It provides traceability to authoritative sources that inform system requirements and design decisions.

---

## 14. Revision History

This section records all changes made to this document, including the date, author, version, and summary of modifications for each revision. It provides an audit trail of the specification's evolution throughout the project lifecycle.

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 31 July 2026 | Dr. Sohil Momin | Initial document structure created |

---

*End of Document — HHMS-DOC-002*
