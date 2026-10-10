"""HHMS IPD clinical documentation tables."""

from alembic import op
import sqlalchemy as sa

revision = "0003_ipd_clinical"
down_revision = "0002_clinical_core"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("IPDAssessment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admission_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("assessment_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("clinical_summary", sa.Text(), nullable=True),
        sa.Column("presenting_complaints", sa.Text(), nullable=True),
        sa.Column("history_present_illness", sa.Text(), nullable=True),
        sa.Column("general_examination", sa.Text(), nullable=True),
        sa.Column("systemic_examination", sa.Text(), nullable=True),
        sa.Column("initial_assessment", sa.Text(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(["admission_id"], ["Admission.id"], name="fk_ipd_assessment_admission"),
        sa.ForeignKeyConstraint(["recorded_by"], ["User.id"], name="fk_ipd_assessment_recorded_by"),
    )
    op.create_index("ix_ipd_assessment_admission_id", "IPDAssessment", ["admission_id"])
    op.create_index("ix_ipd_assessment_recorded_by", "IPDAssessment", ["recorded_by"])
    op.create_table("PainAssessment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admission_id", sa.Integer(), nullable=False),
        sa.Column("assessment_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("pain_present", sa.Boolean(), nullable=True),
        sa.Column("pain_score", sa.Integer(), nullable=True),
        sa.Column("site", sa.String(200), nullable=True),
        sa.Column("character", sa.String(200), nullable=True),
        sa.Column("aggravating_factors", sa.Text(), nullable=True),
        sa.Column("relieving_factors", sa.Text(), nullable=True),
        sa.Column("intervention", sa.Text(), nullable=True),
        sa.Column("reassessment_score", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(["admission_id"], ["Admission.id"], name="fk_pain_assessment_admission"),
        sa.ForeignKeyConstraint(["recorded_by"], ["User.id"], name="fk_pain_assessment_recorded_by"),
    )
    op.create_index("ix_pain_assessment_admission_id", "PainAssessment", ["admission_id"])
    op.create_index("ix_pain_assessment_recorded_by", "PainAssessment", ["recorded_by"])
    op.create_table("NutritionalAssessment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admission_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("assessment_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("appetite", sa.String(30), nullable=True),
        sa.Column("dietary_pattern", sa.String(100), nullable=True),
        sa.Column("weight_kg", sa.Numeric(8,2), nullable=True),
        sa.Column("height_cm", sa.Numeric(8,2), nullable=True),
        sa.Column("bmi", sa.Numeric(8,2), nullable=True),
        sa.Column("risk_level", sa.String(30), nullable=True),
        sa.Column("nutritional_findings", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(["admission_id"], ["Admission.id"], name="fk_nutritional_assessment_admission"),
        sa.ForeignKeyConstraint(["recorded_by"], ["User.id"], name="fk_nutritional_assessment_recorded_by"),
    )
    op.create_index("ix_nutritional_assessment_admission_id", "NutritionalAssessment", ["admission_id"])
    op.create_index("ix_nutritional_assessment_recorded_by", "NutritionalAssessment", ["recorded_by"])
    op.create_table("DietChart",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admission_id", sa.Integer(), nullable=False),
        sa.Column("chart_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("diet_type", sa.String(100), nullable=True),
        sa.Column("breakfast", sa.Text(), nullable=True),
        sa.Column("mid_morning", sa.Text(), nullable=True),
        sa.Column("lunch", sa.Text(), nullable=True),
        sa.Column("evening", sa.Text(), nullable=True),
        sa.Column("dinner", sa.Text(), nullable=True),
        sa.Column("special_instructions", sa.Text(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(["admission_id"], ["Admission.id"], name="fk_diet_chart_admission"),
        sa.ForeignKeyConstraint(["recorded_by"], ["User.id"], name="fk_diet_chart_recorded_by"),
    )
    op.create_index("ix_diet_chart_admission_id", "DietChart", ["admission_id"])
    op.create_index("ix_diet_chart_recorded_by", "DietChart", ["recorded_by"])
    op.create_table("ProgressNote",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admission_id", sa.Integer(), nullable=False),
        sa.Column("note_datetime", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("subjective", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("assessment", sa.Text(), nullable=True),
        sa.Column("plan", sa.Text(), nullable=True),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(["admission_id"], ["Admission.id"], name="fk_progress_note_admission"),
        sa.ForeignKeyConstraint(["recorded_by"], ["User.id"], name="fk_progress_note_recorded_by"),
    )
    op.create_index("ix_progress_note_admission_id", "ProgressNote", ["admission_id"])
    op.create_index("ix_progress_note_recorded_by", "ProgressNote", ["recorded_by"])

def downgrade() -> None:
    op.drop_table("ProgressNote")
    op.drop_table("DietChart")
    op.drop_table("NutritionalAssessment")
    op.drop_table("PainAssessment")
    op.drop_table("IPDAssessment")
