"""Add immutable pharmacy StockCard ledger and dispense linkage."""
from alembic import op
import sqlalchemy as sa

revision = "0017_pharmacy_stock_card_ledger"
down_revision = "0016_operational_year_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "StockCard",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("medicine_id", sa.Integer(), nullable=False),
        sa.Column("stock_batch_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column("quantity_in", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("quantity_out", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("balance_quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("reference_type", sa.String(40), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("transaction_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["medicine_id"], ["Medicine.id"], name="fk_stock_card_medicine"),
        sa.ForeignKeyConstraint(["stock_batch_id"], ["StockBatch.id"], name="fk_stock_card_stock_batch"),
        sa.ForeignKeyConstraint(["created_by"], ["User.id"], name="fk_stock_card_user"),
    )
    op.create_index("ix_stock_card_medicine_id", "StockCard", ["medicine_id"])
    op.create_index("ix_stock_card_stock_batch_id", "StockCard", ["stock_batch_id"])
    op.create_index("ix_stock_card_transaction_type", "StockCard", ["transaction_type"])
    op.create_index("ix_stock_card_reference_id", "StockCard", ["reference_id"])
    op.create_index("ix_stock_card_transaction_datetime", "StockCard", ["transaction_datetime"])
    op.create_index("ix_stock_card_created_by", "StockCard", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_stock_card_created_by", table_name="StockCard")
    op.drop_index("ix_stock_card_transaction_datetime", table_name="StockCard")
    op.drop_index("ix_stock_card_reference_id", table_name="StockCard")
    op.drop_index("ix_stock_card_transaction_type", table_name="StockCard")
    op.drop_index("ix_stock_card_stock_batch_id", table_name="StockCard")
    op.drop_index("ix_stock_card_medicine_id", table_name="StockCard")
    op.drop_table("StockCard")
