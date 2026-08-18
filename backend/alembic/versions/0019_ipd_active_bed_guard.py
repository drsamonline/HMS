"""Prevent more than one active admission from occupying the same bed."""
from alembic import op

revision = "0019_ipd_active_bed_guard"
down_revision = "0018_goods_receipt_stock_integration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_admission_active_bed",
        "Admission",
        ["bed_id"],
        unique=True,
        postgresql_where="admission_status IN ('admitted','active')",
        sqlite_where="admission_status IN ('admitted','active')",
    )


def downgrade() -> None:
    op.drop_index("uq_admission_active_bed", table_name="Admission")
