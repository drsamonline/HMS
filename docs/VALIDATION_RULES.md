# HHMS Validation Rules

This document will contain all data validation rules for the HHMS system.

---

## Overview

Validation rules ensure data integrity and consistency throughout the HHMS application. This document serves as the single source of truth for all validation logic.

*Status: Placeholder - To be populated during development*

---

## Validation Categories

### 1. Patient Data Validation

Rules for patient registration and management.

| Field | Rule | Error Message | Severity |
|-------|------|---------------|----------|
| UHID | Required, Unique | "UHID is required and must be unique" | Critical |
| Name | Required, 2-100 chars | "Name must be between 2 and 100 characters" | Critical |
| Age | 0-150 years | "Age must be between 0 and 150" | Critical |
| Gender | Required, Enum (M/F/O) | "Please select a valid gender" | Critical |
| Phone | Optional, Valid format | "Invalid phone number format" | Warning |
| Email | Optional, Valid email | "Invalid email format" | Warning |

---

### 2. Doctor/Staff Validation

Rules for doctor and staff records.

| Field | Rule | Error Message | Severity |
|-------|------|---------------|----------|
| Registration No | Required, Unique | "Registration number is required and must be unique" | Critical |
| Qualification | Required | "Qualification is required" | Critical |
| Specialization | Optional | - | Info |

---

### 3. Appointment Validation

Rules for appointment scheduling.

| Field | Rule | Error Message | Severity |
|-------|------|---------------|----------|
| Date | Required, Future or Today | "Appointment date must be today or in the future" | Critical |
| Time | Required, Within clinic hours | "Time must be within clinic operating hours" | Critical |
| Patient | Required, Valid UHID | "Valid patient UHID is required" | Critical |
| Doctor | Required, Active doctor | "Please select an active doctor" | Critical |

---

### 4. Prescription Validation

Rules for prescription creation.

| Field | Rule | Error Message | Severity |
|-------|------|---------------|----------|
| Patient | Required | "Patient is required" | Critical |
| Doctor | Required | "Doctor is required" | Critical |
| Remedies | At least one remedy | "At least one remedy is required" | Critical |
| Potency | Required per remedy | "Potency is required for each remedy" | Critical |
| Dosage | Required per remedy | "Dosage instructions are required" | Critical |

---

### 5. Billing Validation

Rules for billing and payments.

| Field | Rule | Error Message | Severity |
|-------|------|---------------|----------|
| Amount | Required, Positive number | "Amount must be a positive number" | Critical |
| Payment Method | Required, Enum | "Please select a valid payment method" | Critical |
| Date | Required, Not in future | "Payment date cannot be in the future" | Critical |

---

### 6. Inventory Validation

Rules for inventory management.

| Field | Rule | Error Message | Severity |
|-------|------|---------------|----------|
| Item Name | Required, Unique | "Item name is required and must be unique" | Critical |
| Quantity | Required, Non-negative | "Quantity cannot be negative" | Critical |
| Expiry Date | Optional, Valid date | "Invalid expiry date format" | Warning |
| Reorder Level | Required, Non-negative | "Reorder level must be non-negative" | Critical |

---

## Validation Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| Critical | Must pass to proceed | Block submission |
| Warning | Should pass but can override | Show warning, allow override |
| Info | Informational only | Display message, no block |

---

## Implementation Guidelines

### Frontend Validation
- Validate on input blur where possible
- Show real-time validation feedback
- Prevent form submission on critical errors
- Display warnings but allow override with confirmation

### Backend Validation
- Never trust frontend validation
- Re-validate all inputs server-side
- Return structured error responses
- Log validation failures for audit

### Database Validation
- Use constraints (NOT NULL, UNIQUE, CHECK)
- Foreign key constraints for relationships
- Triggers for complex validations (if needed)

---

## Error Response Format

```json
{
  "success": false,
  "errors": [
    {
      "field": "patient_name",
      "message": "Name is required",
      "severity": "critical",
      "code": "REQUIRED_FIELD"
    }
  ],
  "warnings": [
    {
      "field": "email",
      "message": "Email format invalid",
      "severity": "warning",
      "code": "INVALID_FORMAT"
    }
  ]
}
```

---

## Future Sections (To Be Completed)

- [ ] Clinical data validation rules
- [ ] Report generation validation
- [ ] User authentication validation
- [ ] File upload validation
- [ ] API request validation
- [ ] Cross-field validation rules
- [ ] Business rule validations

---

## Change History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.0.1 | Session 002 | Initial placeholder | - |

---

*Last Updated: Session 002 - Repository Standardization*

*Status: Placeholder - To be expanded during Milestone 1-2*
