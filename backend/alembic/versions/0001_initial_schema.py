"""
HHMS Version 1.0 initial database schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-11

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin

This migration follows docs/DATABASE_SCHEMA.md.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the complete HHMS Version 1.0 database schema."""

    op.create_table(
        "User",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(150), nullable=True),
        sa.Column("mobile_number", sa.String(20), nullable=True),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint("username", name="uq_user_username"),
        sa.UniqueConstraint("email", name="uq_user_email"),
        sa.PrimaryKeyConstraint("id", name="pk_user"),
    )

    op.create_table(
        "Role",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role_name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint("role_name", name="uq_role_role_name"),
        sa.PrimaryKeyConstraint("id", name="pk_role"),
    )

    op.create_table(
        "Patient",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_number", sa.String(20), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("middle_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("gender", sa.String(20), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("blood_group", sa.String(5), nullable=True),
        sa.Column("mobile_number", sa.String(20), nullable=True),
        sa.Column("email", sa.String(150), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("occupation", sa.String(100), nullable=True),
        sa.Column("marital_status", sa.String(30), nullable=True),
        sa.Column("registration_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint("patient_number", name="uq_patient_number"),
        sa.PrimaryKeyConstraint("id", name="pk_patient"),
    )

    op.create_table(
        "Bed",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bed_number", sa.String(20), nullable=False),
        sa.Column("ward", sa.String(100), nullable=True),
        sa.Column("room_number", sa.String(50), nullable=True),
        sa.Column("bed_type", sa.String(50), nullable=True),
        sa.Column("occupancy_status", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint("bed_number", name="uq_bed_number"),
        sa.PrimaryKeyConstraint("id", name="pk_bed"),
    )

    op.create_table(
        "Medicine",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("medicine_code", sa.String(30), nullable=False),
        sa.Column("medicine_name", sa.String(150), nullable=False),
        sa.Column("scientific_name", sa.String(200), nullable=True),
        sa.Column("medicine_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint("medicine_code", name="uq_medicine_code"),
        sa.PrimaryKeyConstraint("id", name="pk_medicine"),
    )

    op.create_table(
        "Visit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_number", sa.String(20), nullable=False),
        sa.Column("visit_type", sa.String(20), nullable=False),
        sa.Column("visit_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("chief_complaint", sa.Text(), nullable=True),
        sa.Column("consultation_status", sa.String(20), nullable=False),
        sa.Column("consulting_doctor_id", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_visit_patient",
        ),
        sa.ForeignKeyConstraint(
            ["consulting_doctor_id"],
            ["User.id"],
            name="fk_visit_consulting_doctor",
        ),
        sa.UniqueConstraint("visit_number", name="uq_visit_number"),
        sa.PrimaryKeyConstraint("id", name="pk_visit"),
    )

    op.create_table(
        "OPDToken",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visit_id", sa.Integer(), nullable=False),
        sa.Column("token_number", sa.Integer(), nullable=False),
        sa.Column("queue_date", sa.Date(), nullable=False),
        sa.Column("queue_status", sa.String(20), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("called_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["visit_id"],
            ["Visit.id"],
            name="fk_opd_token_visit",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_opd_token"),
    )

    op.create_table(
        "Prescription",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visit_id", sa.Integer(), nullable=False),
        sa.Column("prescription_number", sa.String(20), nullable=False),
        sa.Column("diagnosis", sa.Text(), nullable=True),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
        sa.Column("treatment_plan", sa.Text(), nullable=True),
        sa.Column("prescribed_by", sa.Integer(), nullable=False),
        sa.Column("prescription_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("printed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["visit_id"],
            ["Visit.id"],
            name="fk_prescription_visit",
        ),
        sa.ForeignKeyConstraint(
            ["prescribed_by"],
            ["User.id"],
            name="fk_prescription_prescribed_by",
        ),
        sa.UniqueConstraint(
            "prescription_number",
            name="uq_prescription_number",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_prescription"),
    )

    op.create_table(
        "AuditLog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("activity", sa.String(100), nullable=False),
        sa.Column("entity_name", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["User.id"],
            name="fk_audit_log_user",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
    )

    op.create_table(
        "MedicineBatch",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("medicine_id", sa.Integer(), nullable=False),
        sa.Column("batch_number", sa.String(50), nullable=False),
        sa.Column("potency", sa.String(20), nullable=False),
        sa.Column("manufacturer", sa.String(150), nullable=True),
        sa.Column("manufacture_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("purchase_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("selling_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("quantity_in_stock", sa.Numeric(10, 2), nullable=False),
        sa.Column("minimum_stock", sa.Numeric(10, 2), nullable=True),
        sa.Column("storage_location", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["medicine_id"],
            ["Medicine.id"],
            name="fk_medicine_batch_medicine",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_medicine_batch"),
    )

    op.create_table(
        "DispensingRecord",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("prescription_id", sa.Integer(), nullable=False),
        sa.Column("medicine_batch_id", sa.Integer(), nullable=False),
        sa.Column("quantity_dispensed", sa.Numeric(10, 2), nullable=False),
        sa.Column("dispensing_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("dispensed_by", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["prescription_id"],
            ["Prescription.id"],
            name="fk_dispensing_record_prescription",
        ),
        sa.ForeignKeyConstraint(
            ["medicine_batch_id"],
            ["MedicineBatch.id"],
            name="fk_dispensing_record_medicine_batch",
        ),
        sa.ForeignKeyConstraint(
            ["dispensed_by"],
            ["User.id"],
            name="fk_dispensing_record_user",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_dispensing_record"),
    )

    op.create_table(
        "InventoryItem",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_code", sa.String(30), nullable=False),
        sa.Column("item_name", sa.String(150), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("minimum_stock", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint("item_code", name="uq_inventory_item_code"),
        sa.PrimaryKeyConstraint("id", name="pk_inventory_item"),
    )

    op.create_table(
        "StockTransaction",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("inventory_item_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("transaction_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("reference_number", sa.String(50), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["inventory_item_id"],
            ["InventoryItem.id"],
            name="fk_stock_transaction_inventory_item",
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by"],
            ["User.id"],
            name="fk_stock_transaction_recorded_by",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stock_transaction"),
    )

    op.create_table(
        "Admission",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("admission_number", sa.String(20), nullable=False),
        sa.Column("admission_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("bed_id", sa.Integer(), nullable=False),
        sa.Column("admitted_by", sa.Integer(), nullable=False),
        sa.Column("admission_reason", sa.Text(), nullable=True),
        sa.Column("admission_status", sa.String(20), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_admission_patient",
        ),
        sa.ForeignKeyConstraint(
            ["bed_id"],
            ["Bed.id"],
            name="fk_admission_bed",
        ),
        sa.ForeignKeyConstraint(
            ["admitted_by"],
            ["User.id"],
            name="fk_admission_admitted_by",
        ),
        sa.UniqueConstraint(
            "admission_number",
            name="uq_admission_number",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_admission"),
    )

    op.create_table(
        "Discharge",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admission_id", sa.Integer(), nullable=False),
        sa.Column("discharge_number", sa.String(20), nullable=False),
        sa.Column("discharge_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("discharge_summary", sa.Text(), nullable=True),
        sa.Column("discharge_status", sa.String(20), nullable=False),
        sa.Column("discharged_by", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["admission_id"],
            ["Admission.id"],
            name="fk_discharge_admission",
        ),
        sa.ForeignKeyConstraint(
            ["discharged_by"],
            ["User.id"],
            name="fk_discharge_discharged_by",
        ),
        sa.UniqueConstraint(
            "admission_id",
            name="uq_discharge_admission",
        ),
        sa.UniqueConstraint(
            "discharge_number",
            name="uq_discharge_number",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_discharge"),
    )

    op.create_table(
        "Investigation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("investigation_number", sa.String(20), nullable=False),
        sa.Column("investigation_name", sa.String(150), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("requested_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("investigation_status", sa.String(20), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_investigation_patient",
        ),
        sa.ForeignKeyConstraint(
            ["visit_id"],
            ["Visit.id"],
            name="fk_investigation_visit",
        ),
        sa.ForeignKeyConstraint(
            ["admission_id"],
            ["Admission.id"],
            name="fk_investigation_admission",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["User.id"],
            name="fk_investigation_requested_by",
        ),
        sa.UniqueConstraint(
            "investigation_number",
            name="uq_investigation_number",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_investigation"),
    )

    op.create_table(
        "InvestigationResult",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("result_text", sa.Text(), nullable=True),
        sa.Column("interpretation", sa.Text(), nullable=True),
        sa.Column("result_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column("verification_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_status", sa.String(20), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["Investigation.id"],
            name="fk_investigation_result_investigation",
        ),
        sa.ForeignKeyConstraint(
            ["verified_by"],
            ["User.id"],
            name="fk_investigation_result_verified_by",
        ),
        sa.UniqueConstraint(
            "investigation_id",
            name="uq_investigation_result_investigation",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_investigation_result"),
    )

    op.create_table(
        "Invoice",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("invoice_number", sa.String(20), nullable=False),
        sa.Column("invoice_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_status", sa.String(20), nullable=False),
        sa.Column("generated_by", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_invoice_patient",
        ),
        sa.ForeignKeyConstraint(
            ["visit_id"],
            ["Visit.id"],
            name="fk_invoice_visit",
        ),
        sa.ForeignKeyConstraint(
            ["admission_id"],
            ["Admission.id"],
            name="fk_invoice_admission",
        ),
        sa.ForeignKeyConstraint(
            ["generated_by"],
            ["User.id"],
            name="fk_invoice_generated_by",
        ),
        sa.UniqueConstraint(
            "invoice_number",
            name="uq_invoice_number",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_invoice"),
    )

    op.create_table(
        "Payment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("receipt_number", sa.String(20), nullable=False),
        sa.Column("payment_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column("amount_paid", sa.Numeric(10, 2), nullable=False),
        sa.Column("received_by", sa.Integer(), nullable=False),
        sa.Column("transaction_reference", sa.String(100), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["Invoice.id"],
            name="fk_payment_invoice",
        ),
        sa.ForeignKeyConstraint(
            ["received_by"],
            ["User.id"],
            name="fk_payment_received_by",
        ),
        sa.UniqueConstraint(
            "receipt_number",
            name="uq_payment_receipt_number",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payment"),
    )

    op.create_table(
        "MedicalDocument",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("document_number", sa.String(20), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("document_title", sa.String(200), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("document_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["Patient.id"],
            name="fk_medical_document_patient",
        ),
        sa.ForeignKeyConstraint(
            ["visit_id"],
            ["Visit.id"],
            name="fk_medical_document_visit",
        ),
        sa.ForeignKeyConstraint(
            ["admission_id"],
            ["Admission.id"],
            name="fk_medical_document_admission",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["User.id"],
            name="fk_medical_document_uploaded_by",
        ),
        sa.UniqueConstraint(
            "document_number",
            name="uq_medical_document_number",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_medical_document"),
    )

    # Foreign-key indexes.
    op.create_index("idx_visit_patient_id", "Visit", ["patient_id"])
    op.create_index("idx_visit_consulting_doctor_id", "Visit", ["consulting_doctor_id"])

    op.create_index("idx_opd_token_visit_id", "OPDToken", ["visit_id"])

    op.create_index("idx_prescription_visit_id", "Prescription", ["visit_id"])
    op.create_index("idx_prescription_prescribed_by", "Prescription", ["prescribed_by"])

    op.create_index("idx_audit_log_user_id", "AuditLog", ["user_id"])

    op.create_index("idx_medicine_batch_medicine_id", "MedicineBatch", ["medicine_id"])

    op.create_index(
        "idx_dispensing_record_prescription_id",
        "DispensingRecord",
        ["prescription_id"],
    )
    op.create_index(
        "idx_dispensing_record_medicine_batch_id",
        "DispensingRecord",
        ["medicine_batch_id"],
    )
    op.create_index(
        "idx_dispensing_record_dispensed_by",
        "DispensingRecord",
        ["dispensed_by"],
    )

    op.create_index(
        "idx_stock_transaction_inventory_item_id",
        "StockTransaction",
        ["inventory_item_id"],
    )
    op.create_index(
        "idx_stock_transaction_recorded_by",
        "StockTransaction",
        ["recorded_by"],
    )

    op.create_index("idx_admission_patient_id", "Admission", ["patient_id"])
    op.create_index("idx_admission_bed_id", "Admission", ["bed_id"])
    op.create_index("idx_admission_admitted_by", "Admission", ["admitted_by"])

    op.create_index(
        "idx_discharge_admission_id",
        "Discharge",
        ["admission_id"],
    )
    op.create_index(
        "idx_discharge_discharged_by",
        "Discharge",
        ["discharged_by"],
    )

    op.create_index(
        "idx_investigation_patient_id",
        "Investigation",
        ["patient_id"],
    )
    op.create_index(
        "idx_investigation_visit_id",
        "Investigation",
        ["visit_id"],
    )
    op.create_index(
        "idx_investigation_admission_id",
        "Investigation",
        ["admission_id"],
    )
    op.create_index(
        "idx_investigation_requested_by",
        "Investigation",
        ["requested_by"],
    )

    op.create_index(
        "idx_investigation_result_investigation_id",
        "InvestigationResult",
        ["investigation_id"],
    )
    op.create_index(
        "idx_investigation_result_verified_by",
        "InvestigationResult",
        ["verified_by"],
    )

    op.create_index("idx_invoice_patient_id", "Invoice", ["patient_id"])
    op.create_index("idx_invoice_visit_id", "Invoice", ["visit_id"])
    op.create_index("idx_invoice_admission_id", "Invoice", ["admission_id"])
    op.create_index("idx_invoice_generated_by", "Invoice", ["generated_by"])

    op.create_index("idx_payment_invoice_id", "Payment", ["invoice_id"])
    op.create_index("idx_payment_received_by", "Payment", ["received_by"])

    op.create_index(
        "idx_medical_document_patient_id",
        "MedicalDocument",
        ["patient_id"],
    )
    op.create_index(
        "idx_medical_document_visit_id",
        "MedicalDocument",
        ["visit_id"],
    )
    op.create_index(
        "idx_medical_document_admission_id",
        "MedicalDocument",
        ["admission_id"],
    )
    op.create_index(
        "idx_medical_document_uploaded_by",
        "MedicalDocument",
        ["uploaded_by"],
    )

    # Business/search indexes explicitly identified by the schema.
    op.create_index(
        "idx_patient_first_name",
        "Patient",
        ["first_name"],
    )
    op.create_index(
        "idx_patient_last_name",
        "Patient",
        ["last_name"],
    )
    op.create_index(
        "idx_patient_mobile_number",
        "Patient",
        ["mobile_number"],
    )
    op.create_index(
        "idx_medicine_medicine_name",
        "Medicine",
        ["medicine_name"],
    )
    op.create_index(
        "idx_medicine_batch_batch_number",
        "MedicineBatch",
        ["batch_number"],
    )
    op.create_index(
        "idx_bed_bed_number",
        "Bed",
        ["bed_number"],
    )
    op.create_index(
        "idx_opd_token_queue_date",
        "OPDToken",
        ["queue_date"],
    )
    op.create_index(
        "idx_investigation_investigation_status",
        "Investigation",
        ["investigation_status"],
    )
    op.create_index(
        "idx_invoice_payment_status",
        "Invoice",
        ["payment_status"],
    )

    # Date/time indexes.
    op.create_index(
        "idx_visit_visit_datetime",
        "Visit",
        ["visit_datetime"],
    )
    op.create_index(
        "idx_admission_admission_datetime",
        "Admission",
        ["admission_datetime"],
    )
    op.create_index(
        "idx_discharge_discharge_datetime",
        "Discharge",
        ["discharge_datetime"],
    )
    op.create_index(
        "idx_investigation_requested_datetime",
        "Investigation",
        ["requested_datetime"],
    )
    op.create_index(
        "idx_payment_payment_datetime",
        "Payment",
        ["payment_datetime"],
    )


def downgrade() -> None:
    """Drop the complete HHMS Version 1.0 database schema."""

    tables = [
        "MedicalDocument",
        "Payment",
        "Invoice",
        "InvestigationResult",
        "Investigation",
        "Discharge",
        "Admission",
        "StockTransaction",
        "InventoryItem",
        "DispensingRecord",
        "MedicineBatch",
        "AuditLog",
        "Prescription",
        "OPDToken",
        "Visit",
        "Medicine",
        "Bed",
        "Patient",
        "Role",
        "User",
    ]

    for table in tables:
        op.drop_table(table)