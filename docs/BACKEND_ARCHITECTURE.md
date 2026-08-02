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

# 4. Layered Architecture

HHMS shall implement a Layered Clean Architecture.

The backend shall be organized into the following layers.

```
Presentation Layer
        │
        ▼
REST API Layer
        │
        ▼
Business Service Layer
        │
        ▼
Repository Layer
        │
        ▼
Database Layer
```

Each layer shall have a single responsibility and communicate only with the layer immediately below it.

---

# 5. Dependency Rules

Backend dependencies shall follow a strict downward flow.

Allowed dependencies:

```
API
 ↓
Services
 ↓
Repositories
 ↓
Database
```

The following dependencies are prohibited.

- Repository → API
- Repository → Service
- Database → API
- Database → Service
- Models → API
- Models → Services

Business logic shall never be implemented within:

- API routes
- Database models
- Repository classes

Business logic shall reside exclusively within the Service Layer.

---

# 6. Request Processing Flow

Every request shall follow the same processing sequence.

```
Client

↓

FastAPI Router

↓

Request Validation

↓

Business Service

↓

Repository

↓

SQLAlchemy ORM

↓

Database

↓

Repository

↓

Service

↓

Response Model

↓

Client
```

Each layer shall perform only its designated responsibility.

---

# 7. Backend Standards

The backend shall follow these implementation standards.

## API Layer

Responsible for:

- Request routing
- Request validation
- Dependency injection
- Response generation

The API layer shall not contain business logic.

---

## Service Layer

Responsible for:

- Business rules
- Transactions
- Validation beyond schema validation
- Workflow orchestration

The Service Layer shall contain all business logic.

---

## Repository Layer

Responsible for:

- Database queries
- CRUD operations
- ORM interaction

Repositories shall not contain business rules.

---

## Database Layer

Responsible for:

- Persistence
- Relationships
- Constraints
- Migrations

Database models shall remain persistence objects only.

---

# 8. Project Structure

The backend shall follow the following project structure.

```
backend/

├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── middleware/
│   ├── dependencies/
│   ├── utils/
│   └── main.py
│
├── alembic/
├── tests/
├── uploads/
├── logs/
├── pyproject.toml
└── README.md
```

Each directory shall have a single responsibility.

---

# 9. Configuration Strategy

Application configuration shall be centralized.

Configuration shall be loaded through `pydantic-settings`.

Examples include:

- Database connection
- JWT secret
- Token expiration
- Logging level
- Upload directory
- Application environment

Configuration values shall not be hardcoded.

---

# 10. Logging Strategy

HHMS shall use centralized application logging.

Logging shall support:

- Startup events
- Authentication
- Database errors
- API exceptions
- Inventory operations
- Billing operations
- Audit events

Python's built-in `logging` module shall be used.

---

# 11. Background Processing

Long-running operations shall execute outside the request-response cycle.

Examples include:

- Report generation
- Backup operations
- Email notifications
- File processing

Background processing shall not block API requests.

---

# 12. File Management

Uploaded files shall remain outside the application source code.

Supported file categories include:

- Medical documents
- Investigation reports
- Hospital documents

File metadata shall be stored in the database.

The application shall reference files using relative paths.

---

# 13. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 02 August 2026 | Dr. Sohil Momin | Initial backend architecture completed. |

---

**End of Document — HHMS Backend Architecture**
