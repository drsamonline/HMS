"""Add the pharmacovigilance register.

NCH Code of Ethics 37 requires adverse events to homoeopathic products to be
reported. Until now the readiness report said this duty was not implemented, which
was honest and useless.

Revision ID: 0038_adverse_events
Revises: 0037_nch_duties
"""

from alembic import op
import sqlalchemy as sa

revision = "0038_adverse_events"
down_revision = "0037_nch_duties"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    exists = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='AdverseEvent'"
    ).fetchone()
    if exists:
        return

    op.create_table(
        "AdverseEvent",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("Patient.id"), nullable=False),
        sa.Column("medicine_id", sa.Integer(), sa.ForeignKey("Medicine.id"), nullable=True),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("event_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column("reported", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reported_to", sa.String(200), nullable=True),
        sa.Column("reported_by", sa.Integer(), nullable=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_AdverseEvent_patient_id", "AdverseEvent", ["patient_id"])
    op.create_index("ix_AdverseEvent_reported", "AdverseEvent", ["reported"])


def downgrade() -> None:
    op.drop_table("AdverseEvent")
