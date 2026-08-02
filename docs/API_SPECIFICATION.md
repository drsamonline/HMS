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

# 7. Pharmacy Module Endpoints

## Medicine

GET /medicines

GET /medicines/{id}

POST /medicines

PUT /medicines/{id}

DELETE /medicines/{id}

---

## Medicine Batch

GET /medicine-batches

GET /medicine-batches/{id}

POST /medicine-batches

PUT /medicine-batches/{id}

DELETE /medicine-batches/{id}

---

## Dispensing Record

GET /dispensing-records

GET /dispensing-records/{id}

POST /dispensing-records

PUT /dispensing-records/{id}

DELETE /dispensing-records/{id}

---

# 8. Inventory Module Endpoints

## Inventory Item

GET /inventory-items

GET /inventory-items/{id}

POST /inventory-items

PUT /inventory-items/{id}

DELETE /inventory-items/{id}

---

## Stock Transaction

GET /stock-transactions

GET /stock-transactions/{id}

POST /stock-transactions

PUT /stock-transactions/{id}

DELETE /stock-transactions/{id}

---

# 9. IPD Module Endpoints

## Admission

GET /admissions

GET /admissions/{id}

POST /admissions

PUT /admissions/{id}

DELETE /admissions/{id}

---

## Bed

GET /beds

GET /beds/{id}

POST /beds

PUT /beds/{id}

DELETE /beds/{id}

---

## Discharge

GET /discharges

GET /discharges/{id}

POST /discharges

PUT /discharges/{id}

DELETE /discharges/{id}

---

# 10. Laboratory Module Endpoints

## Investigation

GET /investigations

GET /investigations/{id}

POST /investigations

PUT /investigations/{id}

DELETE /investigations/{id}

---

## Investigation Result

GET /investigation-results

GET /investigation-results/{id}

POST /investigation-results

PUT /investigation-results/{id}

DELETE /investigation-results/{id}

---

# 11. Billing Module Endpoints

## Invoice

GET /invoices

GET /invoices/{id}

POST /invoices

PUT /invoices/{id}

DELETE /invoices/{id}

---

## Payment

GET /payments

GET /payments/{id}

POST /payments

PUT /payments/{id}

DELETE /payments/{id}

---

# 12. Medical Records Module Endpoints

## Medical Document

GET /medical-documents

GET /medical-documents/{id}

POST /medical-documents

PUT /medical-documents/{id}

DELETE /medical-documents/{id}

---

