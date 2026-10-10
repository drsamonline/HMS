# HHMS Naming Conventions

This document establishes naming standards for all code, database, and version control elements in the HHMS project.

---

## 1. Folder Naming

### Rules
- Use lowercase letters only
- Use underscores for multi-word names
- Keep names short but descriptive
- Avoid special characters

### Examples
```
backend/
frontend/
database/
scripts/setup/
docs/01_Project/
```

---

## 2. File Naming

### Rules
- Use UPPERCASE for root configuration files (README.md, LICENSE)
- Use snake_case for documentation files
- Use appropriate extensions (.md, .py, .js, .sql)
- Be descriptive but concise

### Examples
```
PROJECT_CONSTITUTION.md
naming_conventions.md
patient_service.py
main.component.js
schema_v001.sql
```

---

## 3. Class Naming

### Rules
- Use PascalCase (UpperCamelCase)
- Start with a noun
- Be descriptive of the class purpose
- Avoid abbreviations unless universally understood

### Examples
```python
class Patient:
class PrescriptionService:
class DatabaseConnection:
class ReportGenerator:
```

---

## 4. Function Naming

### Rules
- Use snake_case (lowercase with underscores)
- Start with a verb describing the action
- Be clear about what the function does
- Keep names reasonably short

### Examples
```python
def get_patient_by_id(patient_id):
def create_prescription(data):
def validate_input(value):
def calculate_total_amount(items):
```

---

## 5. Variable Naming

### Rules
- Use snake_case for local and global variables
- Use descriptive names that indicate purpose
- Avoid single-letter names except for loop counters
- Use boolean prefixes (is_, has_, can_) for boolean values

### Examples
```python
patient_name = "John Doe"
total_amount = 100.50
is_active = True
has_permission = False
max_retries = 3
```

### Constants
- Use UPPER_SNAKE_CASE for constants
```python
MAX_PAGE_SIZE = 100
DEFAULT_TIMEOUT = 30
API_VERSION = "v1"
```

---

## 6. Database Table Naming

### Rules
- Use snake_case
- Use plural nouns for entity tables
- Prefix junction tables with related entity names
- Keep names consistent with domain terminology

### Examples
```sql
patients
prescriptions
doctors
appointments
patient_medications  -- junction table
```

---

## 7. Database Column Naming

### Rules
- Use snake_case
- Use lowercase only
- Be descriptive but concise
- Use consistent suffixes for common patterns

### Common Suffixes
```
_id      : Primary or foreign key (patient_id, doctor_id)
_name    : Name fields (first_name, last_name)
_date    : Date fields (birth_date, appointment_date)
_at      : Timestamp fields (created_at, updated_at)
_is_     : Boolean flags (is_active, is_deleted)
_count   : Count fields (visit_count, prescription_count)
```

### Examples
```sql
id              -- Primary key
patient_id      -- Foreign key
first_name      -- Name field
email           -- Contact information
birth_date      -- Date field
created_at      -- Creation timestamp
updated_at      -- Last update timestamp
is_active       -- Boolean flag
```

---

## 8. API Endpoint Naming

### Rules
- Use lowercase with hyphens or underscores
- Use RESTful conventions
- Use plural nouns for resources
- Use HTTP methods to indicate actions

### Examples
```
GET    /api/v1/patients
POST   /api/v1/patients
GET    /api/v1/patients/{id}
PUT    /api/v1/patients/{id}
DELETE /api/v1/patients/{id}

GET    /api/v1/appointments/today
POST   /api/v1/prescriptions/generate
```

---

## 9. Git Branch Naming

### Rules
- Use lowercase with hyphens
- Prefix with type: feature/, bugfix/, hotfix/, release/, docs/
- Include ticket/issue number if applicable
- Be descriptive of the branch purpose

### Format
```
type/description
type/ISSUE-number-description
```

### Examples
```
feature/patient-registration
bugfix/prescription-print-error
hotfix/login-security
release/v0.1.0
docs/update-readme
feature/FND-002/repository-standardization
```

---

## 10. Git Commit Message Format

### Rules
- Use imperative mood ("Add" not "Added")
- First line: Short summary (max 50 characters)
- Blank line after summary
- Body: Detailed explanation (wrap at 72 characters)
- Reference issues/decisions when applicable

### Format
```
type: short description

Detailed explanation of the change.

References: #issue-number, D-decision-number
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, no logic change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples
```
feat: add patient registration form

Implemented the patient registration UI with form validation.
Includes fields for name, contact, and medical history.

References: #12, D-001

---

docs: update README with installation steps

Added detailed installation instructions for offline setup.

---

fix: correct prescription calculation error

Fixed rounding issue in dosage calculations.

References: #45
```

---

## 11. Module/Component Naming

### Rules
- Use PascalCase for components
- Prefix with domain context
- End with descriptive suffix (Component, Service, Controller, Repository)

### Examples
```python
PatientFormComponent
PrescriptionService
AppointmentController
PatientRepository
ReportGeneratorService
```

---

## Enforcement

All new code must follow these conventions. Existing code should be updated during refactoring.

Code reviews must verify naming convention compliance using the [REVIEW_CHECKLIST.md](../.ai/REVIEW_CHECKLIST.md).

---

*Last Updated: Session 002 - Repository Standardization*
