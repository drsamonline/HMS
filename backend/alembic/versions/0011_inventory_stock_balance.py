"""Add current quantity to general inventory items."""
from alembic import op
import sqlalchemy as sa
revision="0011_inventory_stock_balance"; down_revision="0010_hospital_system_settings"; branch_labels=None; depends_on=None
def upgrade():
    op.add_column("InventoryItem", sa.Column("quantity_on_hand", sa.Numeric(12,2), nullable=False, server_default="0"))
def downgrade():
    op.drop_column("InventoryItem", "quantity_on_hand")
