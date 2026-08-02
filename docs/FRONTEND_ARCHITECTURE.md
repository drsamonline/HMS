# HHMS Frontend Architecture

---

# 1. Purpose

This document defines the architectural blueprint for the HHMS frontend application.

It establishes the project organization, user interface architecture, component structure, navigation model, state management principles, and frontend development standards.

This document complements:

- MASTER_SPECIFICATION.md
- BACKEND_ARCHITECTURE.md
- API_SPECIFICATION.md

---

# 2. Design Goals

The frontend shall be designed to provide:

- Simple and intuitive workflows.
- Fast navigation.
- Responsive user interface.
- Modular component architecture.
- Consistent user experience.
- Easy maintenance.
- Compatibility with low-resource hardware.
- Future extensibility.

---

# 3. Technology Stack

| Component | Technology |
|-----------|------------|
| Language | TypeScript |
| Framework | React |
| Build Tool | Vite |
| Routing | React Router |
| UI Components | shadcn/ui |
| Styling | Tailwind CSS |
| Forms | React Hook Form |
| Validation | Zod |
| HTTP Client | Axios |
| State Management | React Context + TanStack Query |

---

# 4. Frontend Architecture

The frontend shall follow a feature-first modular architecture.

```
Pages

↓

Feature Modules

↓

Shared Components

↓

API Client

↓

Backend REST API
```

Business logic shall remain within feature modules.

Shared components shall remain presentation-only.

---

# 5. Project Structure

```
frontend/

├── src/
│   ├── api/
│   ├── assets/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── layouts/
│   ├── pages/
│   ├── routes/
│   ├── types/
│   ├── utils/
│   └── main.tsx
│
├── public/
├── package.json
└── vite.config.ts
```

Each directory shall have a single responsibility.

---

# 6. Component Standards

Components shall be categorized as:

- Layout components
- Shared UI components
- Feature components
- Page components

Components shall remain reusable wherever practical.

Business rules shall not be implemented inside reusable UI components.

---

# 7. Navigation

Application navigation shall be organized by functional modules.

Primary navigation shall include:

- Dashboard
- Patients
- OPD
- Pharmacy
- Inventory
- IPD
- Laboratory
- Billing
- Medical Records
- Administration

Routing shall be managed through React Router.

Protected routes shall require authenticated users.

---

# 8. State Management

State shall be divided into:

## Server State

Managed using TanStack Query.

Examples:

- Patient lists
- Visit records
- Medicines
- Reports

---

## Client State

Managed using React Context.

Examples:

- Authentication
- Theme
- Sidebar
- User preferences

Local component state shall be used whenever global state is unnecessary.

---

# 9. API Communication

All HTTP communication shall pass through a centralized API client.

The API client shall provide:

- Authentication token handling
- Request configuration
- Response interception
- Error handling
- Automatic retry where appropriate

Feature modules shall not perform direct HTTP requests.

---

# 10. Error Handling

Frontend error handling shall remain consistent.

The application shall provide:

- Validation messages
- API error messages
- Network error handling
- Unexpected error handling
- User-friendly notifications

Internal implementation details shall never be exposed to users.

---

# 11. Frontend Standards

Frontend development shall follow these principles.

- Feature-first organization.
- Reusable components.
- Responsive layouts.
- Accessibility considerations.
- Type-safe development.
- Consistent naming conventions.
- Minimal business logic inside UI components.
- Separation of presentation and application logic.

---

# 12. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 02 August 2026 | Dr. Sohil Momin | Initial frontend architecture completed. |

---

**End of Document — HHMS Frontend Architecture**