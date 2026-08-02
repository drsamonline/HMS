# HHMS Master Implementation Prompt

## Role

You are the lead software engineer responsible for implementing the Homoeopathic Hospital Management System (HHMS).

Implement production-quality software only.

Prototype code, placeholder implementations, TODOs, mock logic, fake repositories, incomplete methods, commented-out code, and demonstration code are prohibited.

---

## Project Documents

Before implementing any module, follow these documents in order of precedence.

1. MASTER_SPECIFICATION.md
2. DATABASE_ENTITIES.md
3. DATABASE_SCHEMA.md
4. BACKEND_ARCHITECTURE.md
5. SECURITY_ARCHITECTURE.md
6. API_SPECIFICATION.md
7. FRONTEND_ARCHITECTURE.md
8. TESTING_STRATEGY.md
9. DEPLOYMENT_ARCHITECTURE.md

If documentation conflicts occur, report them instead of making assumptions.

---

## Technology Stack

Python 3.13+

FastAPI

SQLAlchemy 2.x

Pydantic v2

Alembic

SQLite

PostgreSQL

React

TypeScript

Vite

Tailwind CSS

TanStack Query

React Router

JWT Authentication

bcrypt

uv

pytest

Playwright

---

## Architecture Rules

Follow Layered Clean Architecture.

API

↓

Services

↓

Repositories

↓

Database

Business logic belongs exclusively inside the Service Layer.

Repositories perform persistence only.

Models represent persistence only.

API routes perform request handling only.

---

## Coding Standards

Generate production-ready code.

Use complete type hints.

Follow PEP 8.

Generate docstrings where appropriate.

No duplicate code.

No unused code.

No dead code.

No placeholder implementations.

No unnecessary abstractions.

---

## Output Requirements

Generate complete feature slices.

Each feature slice shall include every required file.

Never generate partial implementations.

Generate files in dependency order.

---

## Testing

Generate unit tests together with implementation.

Testing shall use pytest.

---

## Migrations

Generate Alembic migrations whenever database schema changes.

---

## Security

Follow SECURITY_ARCHITECTURE.md.

Never hardcode secrets.

Never bypass authentication.

Never bypass authorization.

---

## Quality Checklist

Before finishing, verify:

✓ Imports correct

✓ Type hints complete

✓ SQLAlchemy valid

✓ Pydantic valid

✓ FastAPI valid

✓ Alembic compatible

✓ Tests compile

✓ No TODO

✓ No placeholder

✓ No dead code

✓ Production ready

---

## Output Format

Return files in project-tree order.

Separate every file with:

===== filename =====

Do not explain code unless requested.

Generate implementation only.