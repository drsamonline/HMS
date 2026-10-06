# HHMS Frontend Architecture

## 1. Purpose

This document defines the frontend architecture for the HHMS LAN desktop client.

The frontend is not a public website and is not designed around internet deployment. It is a local application UI that communicates with the HHMS server over the hospital LAN.

## 2. Design Goals

- Fast navigation on low-resource hardware.
- Compact clinical workflows.
- Offline-first LAN operation.
- No direct client database access.
- Simple maintenance by a single developer.
- Reusable HTML/CSS/JavaScript modules.
- Print-first clinical and administrative workflows.
- Progressive saving for incomplete clinical records.

## 3. Client Architecture

```text
HHMS-Client.exe
    |
    +-- Native Windows client host
    |
    +-- Embedded web UI (HTML/CSS/JavaScript)
    |
    +-- Centralized API client
             |
             | HTTP/JSON over LAN
             v
       HHMS-Server.exe
```

The current target for the native web host is WebView2. The exact packaging/runtime strategy will be finalized during the LAN packaging milestone.

## 4. No Heavy Web Framework by Default

The project shall not introduce React, Next.js, Vue, Angular, Electron, Tailwind, or a large UI component framework merely for convenience.

The default frontend implementation shall use:

- HTML
- CSS
- Vanilla JavaScript
- small reusable modules

A framework may be introduced only if a later requirement demonstrates that it materially improves maintainability without violating the low-resource design goal.

## 5. Project Structure

```text
frontend/
├── index.html
├── css/
│   ├── app.css
│   ├── forms.css
│   ├── tables.css
│   └── print.css
├── js/
│   ├── app.js
│   ├── api.js
│   ├── auth.js
│   ├── navigation.js
│   └── feature modules
├── pages/
└── assets/
```

The structure may remain smaller when a feature does not justify additional files.

## 6. Workflow-Centred Navigation

The UI shall be organized around the patient and hospital workflow rather than exposing database tables as the primary navigation model.

Core workspace:

```text
Patient
├── OPD / Consultation
├── Homoeopathic Case Record
├── Diagnosis / ICD-11
├── Prescription
├── Follow-up
├── Investigations
├── IPD
├── Billing
├── Documents
├── MRD
└── Timeline
```

## 7. API Communication

All HTTP requests pass through a centralized API client.

Feature modules must not embed independent connection logic or hard-coded server addresses.

The client shall support:

- authentication
- request/response handling
- network-error handling
- retry
- configured/discovered server address
- preservation of unsaved form data when a request fails

## 8. LAN Discovery

The client shall attempt automatic LAN server discovery.

A manual server address/configuration fallback shall always remain available.

## 9. Progressive Clinical Saving

Clinical forms must permit incomplete records to be saved.

Empty optional sections are valid state and must not be treated as validation errors merely because they are empty.

## 10. Printing

Printing is a core requirement.

Frontend print workflows shall support:

- complete case printing
- selected case sections
- individual clinical documents
- page/document-specific output
- date-wise reports
- custom date-range reports
- batch printing where applicable
- print preview
- PDF export through the system/browser print pipeline

## 11. Performance

Avoid unnecessary dependencies, large client bundles, aggressive polling, per-keystroke network writes, and excessive DOM complexity.

## 12. Security

The client shall never contain database credentials or directly open the database file.

All protected operations go through the authenticated HHMS server API.
