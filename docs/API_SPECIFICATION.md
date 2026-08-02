# HHMS API Specification

---

# 1. Purpose

This document defines the REST API specification for the Homoeopathic Hospital Management System (HHMS).

It establishes the API design standards, endpoint organization, request/response conventions, authentication model, and module-level endpoints that shall be implemented by the backend.

This document serves as the authoritative reference for all REST API development.

---

# 2. API Design Principles

The HHMS REST API shall follow these principles.

- RESTful resource-oriented design.
- JSON request and response bodies.
- Stateless communication.
- Consistent endpoint naming.
- Standard HTTP methods.
- Predictable response formats.
- Versioned API endpoints.
- Automatic OpenAPI documentation through FastAPI.

---

# 3. API Versioning

All endpoints shall be versioned.

Current version:

```
/api/v1/
```

Future versions shall coexist without breaking existing clients.

---

# 4. Authentication

Protected endpoints shall require JWT authentication.

Authentication endpoints:

POST /api/v1/auth/login

POST /api/v1/auth/logout

POST /api/v1/auth/refresh

Authorization shall be enforced through Role-Based Access Control (RBAC).

---

# 5. Standard Response Format

Successful responses shall follow a consistent structure.

```json
{
    "success": true,
    "message": "...",
    "data": {}
}
```

Error responses shall follow:

```json
{
    "success": false,
    "message": "...",
    "errors": []
}
```

---

# 6. Core Module Endpoints

## Patient

GET /patients

GET /patients/{id}

POST /patients

PUT /patients/{id}

DELETE /patients/{id}

---

## Visit

GET /visits

GET /visits/{id}

POST /visits

PUT /visits/{id}

DELETE /visits/{id}

---

## OPD Token

GET /opd-tokens

POST /opd-tokens

PUT /opd-tokens/{id}

DELETE /opd-tokens/{id}

---

## Prescription

GET /prescriptions

GET /prescriptions/{id}

POST /prescriptions

PUT /prescriptions/{id}

DELETE /prescriptions/{id}

---

