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

# 13. Search

Collection endpoints may support search functionality where appropriate.

Search parameters shall be provided using query parameters.

Example:

GET /patients?search=John

Search implementation shall remain consistent across all modules.

---

# 14. Pagination

Collection endpoints shall support pagination.

Standard query parameters:

- page
- page_size

Example:

GET /patients?page=1&page_size=20

Default pagination values shall be defined within the application configuration.

---

# 15. Filtering

Endpoints may support filtering through query parameters.

Examples:

GET /patients?gender=Male

GET /visits?date=2026-08-02

GET /payments?status=Paid

Filtering syntax shall remain consistent across all API modules.

---

# 16. Error Handling

The API shall use standard HTTP status codes.

Examples include:

| Code | Meaning |
|------|----------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 500 | Internal Server Error |

Error responses shall follow the standard response format defined in this document.

---

# 17. API Standards

All API endpoints shall follow these standards.

- RESTful resource naming.
- Stateless communication.
- JSON request and response bodies.
- Consistent endpoint structure.
- Automatic OpenAPI documentation.
- Standard HTTP status codes.
- Versioned endpoints.
- JWT authentication for protected resources.

---

# 18. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 02 August 2026 | Dr. Sohil Momin | Initial API specification completed. |

---

**End of Document — HHMS API Specification**