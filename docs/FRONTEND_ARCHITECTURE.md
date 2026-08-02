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

