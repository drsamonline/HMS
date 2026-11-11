"""Add the table that holds settings changed from the interface.

No seeding. An empty table means "nothing has been overridden", and the effective
value then falls back to the environment and the catalogue default - so an
installation that has never opened the settings screen behaves exactly as it did
before this migration.

Revision ID: 0035_setting_value
Revises: 0034_module_state
"""

from alembic import op
import sqlalchemy as sa

revision = "0035_setting_value"
down_revision = "0034_module_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    exists = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='SettingValue'"
    ).fetchone()
    if exists:
        return

    op.create_table(
        "SettingValue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("setting_key", sa.String(120), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.UniqueConstraint("setting_key", name="uq_setting_value_key"),
    )
    op.create_index("ix_SettingValue_setting_key", "SettingValue", ["setting_key"])


def downgrade() -> None:
    op.drop_table("SettingValue")
