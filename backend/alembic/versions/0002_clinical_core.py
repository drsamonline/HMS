"""HHMS clinical core: case records, diagnoses and follow-ups.

Revision ID: 0002_clinical_core
Revises: 0001_initial_schema
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_clinical_core"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create compact clinical-core tables."""
    op.create_table(
        "CaseRecord",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("admission_id", sa.Integer(), nullable=True),
        sa.Column("case_number", sa.String(20), nullable=False),
        sa.Column("case_status", sa.String(20), nullable=False),
        sa.Column("chief_complaints", sa.Text(), nullable=True),
        sa.Column("history_present_illness", sa.Text(), nullable=True),
        sa.Column("past_history", sa.Text(), nullable=True),
        sa.Column("family_history", sa.Text(), nullable=True),
        sa.Column("personal_history", sa.Text(), nullable=True),
        sa.Column("mental_generals", sa.Text(), nullable=True),
        sa.Column("physical_generals", sa.Text(), nullable=True),
        sa.Column("particulars", sa.Text(), nullable=True),
        sa.Column("female_history", sa.Text(), nullable=True),
        sa.Column("male_history", sa.Text(), nullable=True),
        sa.Column("sexual_reproductive_history", sa.Text(), nullable=True),
        sa.Column("obstetric_history", sa.Text(), nullable=True),
        sa.Column("surgical_history", sa.Text(), nullable=True),
        sa.Column("clinical_examination", sa.Text(), nullable=True),
        sa.Column("totality", sa.Text(), nullable=True),
        sa.Column("characteristic_symptoms", sa.Text(), nullable=True),
        sa.Column("miasmatic_assessment", sa.Text(), nullable=True),
        sa.Column("analytical_notes", sa.Text(), nullable=True),
        sa.Column("remedy_differential", sa.Text(), nullable=True),
        sa.Column("prescribing_rationale", sa.Text(), nullable=True),
        sa.Column("quick_generals", sa.JSON(), nullable=True),
        sa.Column("modalities", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["Patient.id"], name="fk_case_record_patient"),
        sa.ForeignKeyConstraint(["visit_id"], ["Visit.id"], name="fk_case_record_visit"),
        sa.ForeignKeyConstraint(["admission_id"], ["Admission.id"], name="fk_case_record_admission"),
        sa.ForeignKeyConstraint(["created_by"], ["User.id"], name="fk_case_record_created_by"),
        sa.UniqueConstraint("case_number", name="uq_case_record_case_number"),
    )
    op.create_index("ix_case_record_patient_id", "CaseRecord", ["patient_id"])
    op.create_index("ix_case_record_visit_id", "CaseRecord", ["visit_id"])
    op.create_index("ix_case_record_admission_id", "CaseRecord", ["admission_id"])
    op.create_index("ix_case_record_case_number", "CaseRecord", ["case_number"])
    op.create_index("ix_case_record_case_status", "CaseRecord", ["case_status"])
    op.create_index("ix_case_record_created_by", "CaseRecord", ["created_by"])

    op.create_table(
        "Diagnosis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_record_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("diagnosis_name", sa.String(200), nullable=False),
        sa.Column("diagnosis_type", sa.String(30), nullable=False),
        sa.Column("icd11_code", sa.String(30), nullable=True),
        sa.Column("icd11_title", sa.String(300), nullable=True),
        sa.Column("icd11_uri", sa.String(500), nullable=True),
        sa.Column("icd11_release", sa.String(20), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_record_id"], ["CaseRecord.id"], name="fk_diagnosis_case_record"),
        sa.ForeignKeyConstraint(["patient_id"], ["Patient.id"], name="fk_diagnosis_patient"),
        sa.ForeignKeyConstraint(["visit_id"], ["Visit.id"], name="fk_diagnosis_visit"),
        sa.ForeignKeyConstraint(["created_by"], ["User.id"], name="fk_diagnosis_created_by"),
    )
    op.create_index("ix_diagnosis_case_record_id", "Diagnosis", ["case_record_id"])
    op.create_index("ix_diagnosis_patient_id", "Diagnosis", ["patient_id"])
    op.create_index("ix_diagnosis_visit_id", "Diagnosis", ["visit_id"])
    op.create_index("ix_diagnosis_icd11_code", "Diagnosis", ["icd11_code"])
    op.create_index("ix_diagnosis_created_by", "Diagnosis", ["created_by"])

    op.create_table(
        "FollowUp",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_record_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("followup_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("general_status", sa.String(20), nullable=True),
        sa.Column("mental_status", sa.String(20), nullable=True),
        sa.Column("particular_status", sa.String(20), nullable=True),
        sa.Column("remedy_response", sa.String(30), nullable=True),
        sa.Column("decision", sa.String(30), nullable=True),
        sa.Column("new_symptoms", sa.Text(), nullable=True),
        sa.Column("old_symptoms", sa.Text(), nullable=True),
        sa.Column("clinical_assessment", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("previous_prescription_id", sa.Integer(), nullable=True),
        sa.Column("next_prescription_id", sa.Integer(), nullable=True),
        sa.Column("next_followup_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_record_id"], ["CaseRecord.id"], name="fk_followup_case_record"),
        sa.ForeignKeyConstraint(["patient_id"], ["Patient.id"], name="fk_followup_patient"),
        sa.ForeignKeyConstraint(["visit_id"], ["Visit.id"], name="fk_followup_visit"),
        sa.ForeignKeyConstraint(
            ["previous_prescription_id"],
            ["Prescription.id"],
            name="fk_followup_previous_prescription",
        ),
        sa.ForeignKeyConstraint(["next_prescription_id"], ["Prescription.id"], name="fk_followup_next_prescription"),
        sa.ForeignKeyConstraint(["recorded_by"], ["User.id"], name="fk_followup_recorded_by"),
    )
    op.create_index("ix_followup_case_record_id", "FollowUp", ["case_record_id"])
    op.create_index("ix_followup_patient_id", "FollowUp", ["patient_id"])
    op.create_index("ix_followup_visit_id", "FollowUp", ["visit_id"])
    op.create_index("ix_followup_followup_datetime", "FollowUp", ["followup_datetime"])
    op.create_index("ix_followup_previous_prescription_id", "FollowUp", ["previous_prescription_id"])
    op.create_index("ix_followup_next_prescription_id", "FollowUp", ["next_prescription_id"])
    op.create_index("ix_followup_recorded_by", "FollowUp", ["recorded_by"])


def downgrade() -> None:
    """Remove clinical-core tables."""
    op.drop_table("FollowUp")
    op.drop_table("Diagnosis")
    op.drop_table("CaseRecord")
