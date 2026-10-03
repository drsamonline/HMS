"""Add invoice line items."""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
revision = "0013_invoice_items"
down_revision = "0012_procurement"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "InvoiceItem",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(40), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["invoice_id"], ["Invoice.id"], name="fk_invoice_item_invoice", ondelete="CASCADE"),
    )
    op.create_index("ix_InvoiceItem_invoice_id", "InvoiceItem", ["invoice_id"])

def downgrade() -> None:
    op.drop_index("ix_InvoiceItem_invoice_id", table_name="InvoiceItem")
    op.drop_table("InvoiceItem")
