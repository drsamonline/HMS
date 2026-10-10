# HHMS Implementation Rules

**Version:** 1.0  
**Status:** FINAL (Frozen)  
**Applies To:** Entire HHMS Repository

---

# 1. Project Principle

- Documentation is frozen after approval.
- Architecture is frozen after approval.
- Implement only approved features.
- No speculative development.
- Production-ready code only.

---

# 2. Architecture Rules

- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Pydantic Settings
- Alembic
- Repository Pattern
- Service Layer
- Dependency Injection
- Layered Architecture
- JWT Authentication
- REST API

Never violate architecture for convenience.

---

# 3. Coding Standards

## Python

- Python 3.13+
- Full type hints
- Google-style docstrings
- Ruff compliant
- Black formatted
- PEP8 compliant

## Naming

Classes

- PascalCase

Functions

- snake_case

Variables

- snake_case

Constants

- UPPER_CASE

Private members

- _leading_underscore

---

# 4. Imports

- Standard Library
- Third-party Packages
- Local Packages

No wildcard imports.

No circular imports.

---

# 5. Configuration

Configuration only through:

```
.env
```

Never hardcode:

- passwords
- API keys
- database credentials
- JWT secrets
- URLs

Use:

```
config/settings.py
```

---

# 6. Logging

Centralized logging only.

Requirements

- RotatingFileHandler
- Console logging
- Configurable level
- Structured messages

No print() statements.

---

# 7. Error Handling

Use custom exceptions.

Never swallow exceptions.

Every API error returns a structured response.

Unexpected exceptions are logged.

---

# 8. Security

- Password hashing
- JWT
- Role-based authorization
- Input validation
- Output validation
- No SQL injection
- No hardcoded secrets

---

# 9. Database Rules

- SQLAlchemy ORM only
- Alembic migrations
- Foreign keys
- Constraints
- Relationships
- Transactions
- Repository Pattern

No raw SQL unless absolutely necessary.

---

# 10. API Rules

REST only.

Consistent endpoints.

Consistent status codes.

Consistent response models.

Validation through Pydantic.

---

# 11. Folder Responsibilities

## config/

Configuration only.

No business logic.

---

## core/

Security

Constants

Exceptions

Utilities

---

## db/

Database connection

Session

Base

Initialization

---

## models/

ORM models only.

---

## schemas/

Pydantic models only.

---

## repositories/

Database access only.

No business logic.

---

## services/

Business logic only.

No SQL.

---

## api/

Routers only.

No business logic.

---

## dependencies/

Dependency Injection only.

---

## middleware/

Middleware only.

---

## utils/

Reusable helper functions.

---

# 12. Package Order

01 Config

02 Database

03 Core

04 Dependencies

05 Middleware

06 Bootstrap

07 Authentication

08 Patient

09 Visit

10 Prescription

11 OPD

12 Pharmacy

13 Inventory

14 IPD

15 Laboratory

16 Billing

17 Medical Records

18 Frontend

19 Testing

20 Deployment

Do not skip package order.

---

# 13. Package Completion Criteria

A package is complete only if:

- Imports successfully
- Runs successfully
- No syntax errors
- No lint errors
- No TODOs
- No placeholder code
- Full typing
- Documentation complete
- Matches architecture
- Ready to commit

---

# 14. Git Rules

One package

↓

One commit

Commit only working code.

Never commit broken builds.

Commit format

```
feat(config): implement configuration package

feat(db): implement database package

feat(patient): implement patient module

fix(auth): resolve jwt validation issue

refactor(core): improve dependency injection

docs(api): update endpoint documentation
```

---

# 15. Change Rules

Modify existing files whenever appropriate.

Avoid unnecessary rewrites.

Avoid unrelated refactoring.

Keep commits focused.

---

# 16. AI Workflow

## ChatGPT

Primary Architect

Primary Developer

Primary Reviewer

Primary QA

Primary Integration Engineer

---

## External AI (Optional)

DeepSeek

Gemini

Qwen Max

Purpose

- Independent review
- Bug detection
- Optimization suggestions
- Security review
- Performance review

Never use external AI as the primary code generator.

All suggestions must be reviewed before implementation.

---

# 17. Development Workflow

Read repository

↓

Implement current package

↓

Internal review

↓

Run application

↓

Fix issues

↓

Optional external review

↓

Final review

↓

Commit

↓

Next package

---

# 18. Quality Checklist

Before every commit verify:

- Architecture preserved
- Imports correct
- Naming consistent
- Formatting correct
- Type hints complete
- Logging implemented
- Exceptions handled
- Security maintained
- Documentation updated
- Runs successfully

---

# 19. Definition of Done

Code compiles.

Application runs.

Architecture preserved.

No placeholders.

No TODOs.

No dead code.

No duplicated logic.

Production ready.

Committed.

---

# 20. Forbidden Practices

- Hardcoded secrets
- Hardcoded paths
- Duplicate code
- Circular imports
- Wildcard imports
- Global mutable state
- Business logic inside routers
- SQL inside services
- Configuration inside business logic
- Direct database access outside repositories
- Silent exception handling
- Commented-out code
- Sample/demo code in production

---

# 21. Project Freeze Policy

The following are frozen unless explicitly approved:

- Documentation
- Architecture
- Database design
- Folder structure
- Package order
- Coding standards
- Implementation workflow

Only production code changes after this point.

---

**End of Document**