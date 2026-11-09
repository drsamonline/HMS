"""Two fields the NCH Code of Ethics makes necessary.

Regulation 7(2) requires a practitioner's registration number on every prescription
and medical certificate, and failing to display it is professional misconduct. That
makes it a fact about the person, so it lives on User.

Regulation 31(1) requires the reason for a change of treatment to be stated at the
next consultation. That makes it a fact about the follow-up.

Revision ID: 0037_nch_duties
Revises: 0036_setup_state
"""

from alembic import op
import sqlalchemy as sa

revision = "0037_nch_duties"
down_revision = "0036_setup_state"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    return any(row[1] == column for row in bind.exec_driver_sql(f"PRAGMA table_info(\"{table}\")"))


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_column(bind, "User", "registration_number"):
        op.add_column("User", sa.Column("registration_number", sa.String(40), nullable=True))

    if not _has_column(bind, "Followup", "reason_for_change"):
        op.add_column("Followup", sa.Column("reason_for_change", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "Followup", "reason_for_change"):
        op.drop_column("Followup", "reason_for_change")
    if _has_column(bind, "User", "registration_number"):
        op.drop_column("User", "registration_number")
