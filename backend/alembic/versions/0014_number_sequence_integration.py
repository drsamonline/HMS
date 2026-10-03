"""Integrate configurable number sequences across operational identifiers."""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "0014_number_sequence_integration"
down_revision = "0013_invoice_items"
branch_labels = None
depends_on = None

SEQUENCES = [
    ("case_number", "CASE", "", "never", 6),
    ("discharge_number", "DIS", "", "yearly", 6),
    ("prescription_number", "RX", "", "never", 6),
    ("investigation_number", "INV", "", "yearly", 6),
    ("receipt_number", "RCT", "", "yearly", 6),
]

def upgrade() -> None:
    op.add_column("NumberSequence", sa.Column("last_reset_at", sa.DateTime(timezone=True), nullable=True))
    table = sa.table(
        "NumberSequence",
        sa.column("sequence_name", sa.String),
        sa.column("prefix", sa.String),
        sa.column("suffix", sa.String),
        sa.column("current_value", sa.Integer),
        sa.column("padding_length", sa.Integer),
        sa.column("reset_frequency", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    bind = op.get_bind()
    existing = {r[0] for r in bind.execute(sa.text("SELECT sequence_name FROM NumberSequence")).fetchall()}
    rows = [
        {"sequence_name": n, "prefix": p, "suffix": s, "current_value": 0, "padding_length": pad, "reset_frequency": f, "is_active": True}
        for n,p,s,f,pad in SEQUENCES if n not in existing
    ]
    if rows:
        op.bulk_insert(table, rows)

def downgrade() -> None:
    op.drop_column("NumberSequence", "last_reset_at")
