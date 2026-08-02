# HHMS Backend Architecture

---

# 1. Purpose

This document defines the architectural blueprint for the Homoeopathic Hospital Management System (HHMS) backend.

It establishes the software architecture, implementation principles, project organization, dependency rules, and development standards that shall govern all backend development.

This document serves as the authoritative architectural reference for backend implementation.

Business requirements remain governed by:

- MASTER_SPECIFICATION.md
- DATABASE_ENTITIES.md
- DATABASE_SCHEMA.md

---

# 2. Design Goals

The HHMS backend shall be designed to achieve the following goals.

## Simplicity

The architecture shall remain easy to understand and maintain by a single developer.

---

## Modularity

Each functional module shall remain independent wherever possible.

---

## Maintainability

Business logic shall be isolated from infrastructure and persistence.

---

## Scalability

The architecture shall support future modules without requiring redesign.

---

## Reliability

The backend shall preserve data integrity and provide consistent system behavior.

---

## Performance

The application shall operate efficiently on low-resource hardware while remaining scalable to PostgreSQL deployments.

---

## Testability

Business services shall be independently testable without requiring API or database interaction.

---

## Offline First

The backend shall operate fully using a local SQLite database while remaining compatible with PostgreSQL.

---

## Security

Authentication, authorization, validation, and audit logging shall be implemented consistently throughout the application.

---

# 3. Technology Stack

The backend shall use the following technology stack.

| Component | Technology |
|-----------|------------|
| Language | Python 3.13+ |
| Web Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Validation | Pydantic v2 |
| Database | SQLite / PostgreSQL |
| Database Migration | Alembic |
| Authentication | JWT |
| Password Hashing | bcrypt |
| Dependency Management | uv |
| Package Manager | uv |
| Testing | pytest |
| ASGI Server | Uvicorn |
| Configuration | pydantic-settings |
| Logging | Python logging |

---

