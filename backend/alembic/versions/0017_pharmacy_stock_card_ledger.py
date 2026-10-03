"""Add immutable pharmacy stock card ledger."""
from alembic import op
import sqlalchemy as sa
revision="0017_pharmacy_stock_card_ledger"
down_revision="0016_operational_year_settings"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("StockCard",
        sa.Column("id",sa.Integer(),primary_key=True,autoincrement=True),
        sa.Column("medicine_id",sa.Integer(),nullable=False),
        sa.Column("stock_batch_id",sa.Integer(),nullable=False),
        sa.Column("transaction_type",sa.String(length=30),nullable=False),
        sa.Column("quantity_in",sa.Numeric(10,2),nullable=False,server_default="0"),
        sa.Column("quantity_out",sa.Numeric(10,2),nullable=False,server_default="0"),
        sa.Column("balance_quantity",sa.Numeric(12,2),nullable=False),
        sa.Column("reference_type",sa.String(length=30),nullable=True),
        sa.Column("reference_id",sa.Integer(),nullable=True),
        sa.Column("transaction_datetime",sa.DateTime(timezone=True),nullable=False),
        sa.Column("created_by",sa.Integer(),nullable=False),
        sa.Column("remarks",sa.Text(),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["medicine_id"],["Medicine.id"],name="fk_stock_card_medicine"),
        sa.ForeignKeyConstraint(["stock_batch_id"],["StockBatch.id"],name="fk_stock_card_stock_batch"),
        sa.ForeignKeyConstraint(["created_by"],["User.id"],name="fk_stock_card_user"),
    )
    for name,col in [("ix_stock_card_medicine","medicine_id"),("ix_stock_card_batch","stock_batch_id"),("ix_stock_card_type","transaction_type"),("ix_stock_card_ref_type","reference_type"),("ix_stock_card_ref_id","reference_id"),("ix_stock_card_datetime","transaction_datetime"),("ix_stock_card_user","created_by")]:
        op.create_index(name,"StockCard",[col])

def downgrade():
    for name in ["ix_stock_card_user","ix_stock_card_datetime","ix_stock_card_ref_id","ix_stock_card_ref_type","ix_stock_card_type","ix_stock_card_batch","ix_stock_card_medicine"]:
        op.drop_index(name,table_name="StockCard")
    op.drop_table("StockCard")
