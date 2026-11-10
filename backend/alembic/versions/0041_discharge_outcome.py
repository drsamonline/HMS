"""Record how an inpatient episode ended, not only that it ended.

Mortality and discharge-against-medical-advice could not be measured because nothing
distinguished a patient who went home well from one who died. ``discharge_status``
answers a different question - whether the discharge record is valid - and using it
for outcomes would have been a quiet lie.

Nullable, and existing rows are left null. An episode whose outcome nobody recorded
has an unknown outcome, not a good one, and the indicators report it as unavailable
rather than assuming.

Revision ID: 0041_discharge_outcome
Revises: 0040_investigation_accession
"""

from alembic import op
import sqlalchemy as sa

revision = "0041_discharge_outcome"
down_revision = "0040_investigation_accession"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    return any(
        row[1] == column for row in bind.exec_driver_sql(f'PRAGMA table_info("{table}")')
    )


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "Discharge", "discharge_outcome"):
        op.add_column(
            "Discharge", sa.Column("discharge_outcome", sa.String(20), nullable=True)
        )
        op.create_index(
            "ix_Discharge_discharge_outcome", "Discharge", ["discharge_outcome"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "Discharge", "discharge_outcome"):
        op.drop_index("ix_Discharge_discharge_outcome", table_name="Discharge")
        op.drop_column("Discharge", "discharge_outcome")
