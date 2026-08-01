# DATABASE SCHEMA

## Core

### User

**Table:** `user`

**Columns:**
- user_id (PK)
- username
- password_hash
- email
- full_name
- role_id (FK)
- department_id (FK)
- is_active
- created_at
- updated_at

**Primary Key:** user_id

**Foreign Keys:**
- role_id → Role.role_id
- department_id → Department.department_id

**Indexes:** username, email

---

### Role

**Table:** `role`

**Columns:**
- role_id (PK)
- role_name
- description
- is_active
- created_at
- updated_at

**Primary Key:** role_id

**Indexes:** role_name

---

### AuditLog

**Table:** `audit_log`

**Columns:**
- audit_id (PK)
- user_id (FK)
- action_type
- table_name
- record_id
- old_value
- new_value
- ip_address
- created_at

**Primary Key:** audit_id

**Foreign Keys:**
- user_id → User.user_id

**Indexes:** user_id, table_name, created_at

---

## Patients

### Patient

**Table:** `patient`

**Columns:**
- patient_id (PK)
- registration_no
- first_name
- last_name
- gender
- date_of_birth
- mobile
- alternate_mobile
- email
- address
- city
- state
- pincode
- guardian_id (FK)
- blood_group
- is_active
- created_at
- updated_at

**Primary Key:** patient_id

**Foreign Keys:**
- guardian_id → Guardian.guardian_id

**Indexes:** registration_no, mobile, last_name

---

### Guardian

**Table:** `guardian`

**Columns:**
- guardian_id (PK)
- first_name
- last_name
- relationship
- mobile
- address
- created_at
- updated_at

**Primary Key:** guardian_id

**Indexes:** mobile, last_name

---

## Clinical

### Consultation

**Table:** `consultation`

**Columns:**
- consultation_id (PK)
- patient_id (FK)
- user_id (FK)
- consultation_date
- chief_complaints
- history_present_illness
- past_history
- family_history
- vital_bp_systolic
- vital_bp_diastolic
- vital_pulse
- vital_temperature
- vital_respiratory_rate
- vital_weight
- vital_height
- symptoms
- examination_findings
- diagnosis_id (FK)
- clinical_note_id (FK)
- prescription_id (FK)
- follow_up_date
- created_at
- updated_at

**Primary Key:** consultation_id

**Foreign Keys:**
- patient_id → Patient.patient_id
- user_id → User.user_id
- diagnosis_id → Diagnosis.diagnosis_id

**Indexes:** patient_id, consultation_date, user_id

---

### Diagnosis

**Table:** `diagnosis`

**Columns:**
- diagnosis_id (PK)
- diagnosis_code
- diagnosis_name
- diagnosis_type
- notes
- created_at
- updated_at

**Primary Key:** diagnosis_id

**Indexes:** diagnosis_code, diagnosis_name

---

### ClinicalNote

**Table:** `clinical_note`

**Columns:**
- clinical_note_id (PK)
- consultation_id (FK)
- note_type
- note_text
- created_at
- updated_at

**Primary Key:** clinical_note_id

**Foreign Keys:**
- consultation_id → Consultation.consultation_id

**Indexes:** consultation_id

---

## Prescription

### Prescription

**Table:** `prescription`

**Columns:**
- prescription_id (PK)
- consultation_id (FK)
- prescription_date
- instructions
- created_at
- updated_at

**Primary Key:** prescription_id

**Foreign Keys:**
- consultation_id → Consultation.consultation_id

**Indexes:** consultation_id, prescription_date

---

### PrescriptionItem

**Table:** `prescription_item`

**Columns:**
- prescription_item_id (PK)
- prescription_id (FK)
- medicine_id (FK)
- dosage
- frequency
- duration_days
- instructions
- quantity
- created_at
- updated_at

**Primary Key:** prescription_item_id

**Foreign Keys:**
- prescription_id → Prescription.prescription_id
- medicine_id → Medicine.medicine_id

**Indexes:** prescription_id, medicine_id

---

## Pharmacy

### Medicine

**Table:** `medicine`

**Columns:**
- medicine_id (PK)
- name
- generic_name
- brand_name
- manufacturer
- category
- unit_of_measure
- reorder_level
- is_active
- created_at
- updated_at

**Primary Key:** medicine_id

**Indexes:** name, generic_name, brand_name

---

### DispenseRecord

**Table:** `dispense_record`

**Columns:**
- dispense_id (PK)
- prescription_item_id (FK)
- medicine_id (FK)
- stock_batch_id (FK)
- quantity_dispensed
- dispense_date
- dispensed_by (FK)
- notes
- created_at
- updated_at

**Primary Key:** dispense_id

**Foreign Keys:**
- prescription_item_id → PrescriptionItem.prescription_item_id
- medicine_id → Medicine.medicine_id
- stock_batch_id → StockBatch.stock_batch_id
- dispensed_by → User.user_id

**Indexes:** prescription_item_id, medicine_id, dispense_date

---

### StockAdjustment

**Table:** `stock_adjustment`

**Columns:**
- adjustment_id (PK)
- medicine_id (FK)
- stock_batch_id (FK)
- adjustment_type
- quantity
- reason
- adjusted_by (FK)
- notes
- created_at
- updated_at

**Primary Key:** adjustment_id

**Foreign Keys:**
- medicine_id → Medicine.medicine_id
- stock_batch_id → StockBatch.stock_batch_id
- adjusted_by → User.user_id

**Indexes:** medicine_id, adjustment_type, created_at

---

## Inventory

### Supplier

**Table:** `supplier`

**Columns:**
- supplier_id (PK)
- supplier_name
- contact_person
- mobile
- email
- address
- city
- state
- pincode
- gst_no
- drug_license_no
- is_active
- created_at
- updated_at

**Primary Key:** supplier_id

**Indexes:** supplier_name, mobile, gst_no

---

### StockBatch

**Table:** `stock_batch`

**Columns:**
- stock_batch_id (PK)
- medicine_id (FK)
- batch_no
- expiry_date
- manufacture_date
- quantity_received
- quantity_remaining
- unit_cost
- total_cost
- supplier_id (FK)
- goods_receipt_id (FK)
- is_active
- created_at
- updated_at

**Primary Key:** stock_batch_id

**Foreign Keys:**
- medicine_id → Medicine.medicine_id
- supplier_id → Supplier.supplier_id
- goods_receipt_id → GoodsReceipt.goods_receipt_id

**Indexes:** batch_no, expiry_date, medicine_id

---

### PurchaseOrder

**Table:** `purchase_order`

**Columns:**
- purchase_order_id (PK)
- order_no
- supplier_id (FK)
- order_date
- expected_delivery_date
- status
- total_amount
- notes
- created_by (FK)
- created_at
- updated_at

**Primary Key:** purchase_order_id

**Foreign Keys:**
- supplier_id → Supplier.supplier_id
- created_by → User.user_id

**Indexes:** order_no, supplier_id, order_date, status

---

### PurchaseOrderItem

**Table:** `purchase_order_item`

**Columns:**
- po_item_id (PK)
- purchase_order_id (FK)
- medicine_id (FK)
- quantity_ordered
- unit_cost
- total_cost
- quantity_received
- created_at
- updated_at

**Primary Key:** po_item_id

**Foreign Keys:**
- purchase_order_id → PurchaseOrder.purchase_order_id
- medicine_id → Medicine.medicine_id

**Indexes:** purchase_order_id, medicine_id

---

### GoodsReceipt

**Table:** `goods_receipt`

**Columns:**
- goods_receipt_id (PK)
- purchase_order_id (FK)
- receipt_no
- receipt_date
- supplier_id (FK)
- total_quantity
- accepted_quantity
- rejected_quantity
- remarks
- received_by (FK)
- created_at
- updated_at

**Primary Key:** goods_receipt_id

**Foreign Keys:**
- purchase_order_id → PurchaseOrder.purchase_order_id
- supplier_id → Supplier.supplier_id
- received_by → User.user_id

**Indexes:** receipt_no, purchase_order_id, receipt_date

---

### StockCard

**Table:** `stock_card`

**Columns:**
- stock_card_id (PK)
- medicine_id (FK)
- stock_batch_id (FK)
- transaction_type
- quantity_in
- quantity_out
- balance_quantity
- reference_type
- reference_id
- transaction_date
- created_by (FK)
- created_at

**Primary Key:** stock_card_id

**Foreign Keys:**
- medicine_id → Medicine.medicine_id
- stock_batch_id → StockBatch.stock_batch_id
- created_by → User.user_id

**Indexes:** medicine_id, stock_batch_id, transaction_date

---

## Billing

### Invoice

**Table:** `invoice`

**Columns:**
- invoice_id (PK)
- invoice_no
- patient_id (FK)
- consultation_id (FK)
- admission_id (FK)
- invoice_date
- subtotal
- discount_amount
- tax_amount
- total_amount
- paid_amount
- balance_amount
- status
- notes
- created_by (FK)
- created_at
- updated_at

**Primary Key:** invoice_id

**Foreign Keys:**
- patient_id → Patient.patient_id
- consultation_id → Consultation.consultation_id
- admission_id → Admission.admission_id
- created_by → User.user_id

**Indexes:** invoice_no, patient_id, invoice_date, status

---

### InvoiceItem

**Table:** `invoice_item`

**Columns:**
- invoice_item_id (PK)
- invoice_id (FK)
- item_type
- item_id
- description
- quantity
- unit_price
- discount
- tax
- total_amount
- created_at
- updated_at

**Primary Key:** invoice_item_id

**Foreign Keys:**
- invoice_id → Invoice.invoice_id

**Indexes:** invoice_id

---

### Payment

**Table:** `payment`

**Columns:**
- payment_id (PK)
- invoice_id (FK)
- payment_no
- payment_date
- payment_method
- amount
- reference_no
- remarks
- received_by (FK)
- created_at
- updated_at

**Primary Key:** payment_id

**Foreign Keys:**
- invoice_id → Invoice.invoice_id
- received_by → User.user_id

**Indexes:** invoice_id, payment_no, payment_date

---

## IPD

### Ward

**Table:** `ward`

**Columns:**
- ward_id (PK)
- ward_name
- ward_type
- floor
- description
- is_active
- created_at
- updated_at

**Primary Key:** ward_id

**Indexes:** ward_name

---

### Room

**Table:** `room`

**Columns:**
- room_id (PK)
- ward_id (FK)
- room_no
- room_type
- bed_capacity
- rate_per_day
- is_active
- created_at
- updated_at

**Primary Key:** room_id

**Foreign Keys:**
- ward_id → Ward.ward_id

**Indexes:** room_no, ward_id

---

### Bed

**Table:** `bed`

**Columns:**
- bed_id (PK)
- room_id (FK)
- bed_no
- bed_type
- rate_per_day
- is_active
- created_at
- updated_at

**Primary Key:** bed_id

**Foreign Keys:**
- room_id → Room.room_id

**Indexes:** bed_no, room_id

---

### Admission

**Table:** `admission`

**Columns:**
- admission_id (PK)
- admission_no
- patient_id (FK)
- admission_date
- admission_time
- ward_id (FK)
- room_id (FK)
- bed_id (FK)
- diagnosis
- admitting_doctor_id (FK)
- estimated_discharge_date
- status
- advance_paid
- notes
- created_at
- updated_at

**Primary Key:** admission_id

**Foreign Keys:**
- patient_id → Patient.patient_id
- ward_id → Ward.ward_id
- room_id → Room.room_id
- bed_id → Bed.bed_id
- admitting_doctor_id → User.user_id

**Indexes:** admission_no, patient_id, admission_date, status

---

### Discharge

**Table:** `discharge`

**Columns:**
- discharge_id (PK)
- admission_id (FK)
- discharge_date
- discharge_time
- discharge_type
- discharge_summary
- follow_up_instructions
- discharged_by (FK)
- invoice_id (FK)
- created_at
- updated_at

**Primary Key:** discharge_id

**Foreign Keys:**
- admission_id → Admission.admission_id
- discharged_by → User.user_id
- invoice_id → Invoice.invoice_id

**Indexes:** admission_id, discharge_date

---

### BedAssignment

**Table:** `bed_assignment`

**Columns:**
- bed_assignment_id (PK)
- admission_id (FK)
- bed_id (FK)
- assignment_date
- assignment_time
- release_date
- release_time
- billing_days
- rate_applied
- total_charge
- created_at
- updated_at

**Primary Key:** bed_assignment_id

**Foreign Keys:**
- admission_id → Admission.admission_id
- bed_id → Bed.bed_id

**Indexes:** admission_id, bed_id

---

## MRD

### PatientFile

**Table:** `patient_file`

**Columns:**
- patient_file_id (PK)
- patient_id (FK)
- file_no
- file_type
- location
- shelf_no
- rack_no
- status
- created_at
- updated_at

**Primary Key:** patient_file_id

**Foreign Keys:**
- patient_id → Patient.patient_id

**Indexes:** file_no, patient_id

---

### ArchiveRecord

**Table:** `archive_record`

**Columns:**
- archive_id (PK)
- patient_file_id (FK)
- archive_date
- archive_location
- box_no
- retention_period
- status
- created_at
- updated_at

**Primary Key:** archive_id

**Foreign Keys:**
- patient_file_id → PatientFile.patient_file_id

**Indexes:** patient_file_id, archive_date

---

## Administration

### Department

**Table:** `department`

**Columns:**
- department_id (PK)
- department_name
- department_code
- description
- is_active
- created_at
- updated_at

**Primary Key:** department_id

**Indexes:** department_name, department_code

---

### Designation

**Table:** `designation`

**Columns:**
- designation_id (PK)
- designation_name
- designation_code
- description
- is_active
- created_at
- updated_at

**Primary Key:** designation_id

**Indexes:** designation_name

---

## Settings

### Hospital

**Table:** `hospital`

**Columns:**
- hospital_id (PK)
- hospital_name
- hospital_code
- address
- city
- state
- pincode
- phone
- email
- website
- logo_path
- license_no
- registration_no
- tax_id
- created_at
- updated_at

**Primary Key:** hospital_id

**Indexes:** hospital_name, hospital_code

---

### SystemSetting

**Table:** `system_setting`

**Columns:**
- setting_id (PK)
- setting_key
- setting_value
- setting_type
- description
- is_editable
- created_at
- updated_at

**Primary Key:** setting_id

**Indexes:** setting_key

---

### NumberSequence

**Table:** `number_sequence`

**Columns:**
- sequence_id (PK)
- sequence_name
- prefix
- suffix
- current_value
- padding_length
- reset_frequency
- is_active
- created_at
- updated_at

**Primary Key:** sequence_id

**Indexes:** sequence_name

---

## Summary

**Total Tables:** 35

**Modules:**
- Core: 3 tables
- Patients: 2 tables
- Clinical: 3 tables
- Prescription: 2 tables
- Pharmacy: 3 tables
- Inventory: 6 tables
- Billing: 3 tables
- IPD: 6 tables
- MRD: 2 tables
- Administration: 2 tables
- Settings: 3 tables

**Status:** READY FOR IMPLEMENTATION
