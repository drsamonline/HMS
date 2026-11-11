"""Permissions granted to one person, on top of their role.

Roles cover the common case; this covers the locum, the senior technician, the matron
covering a fortnight. Additive only - see the model's docstring for why there is no deny.

Revision ID: 0043_user_permissions
Revises: 0042_institute_registrations
"""

from alembic import op
import sqlalchemy as sa

revision = "0043_user_permissions"
down_revision = "0042_institute_registrations"
branch_labels = None
depends_on = None


def _has_table(bind, table: str) -> bool:
    return bind.exec_driver_sql(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
    ).fetchone() is not None


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "UserPermission"):
        return

    op.create_table(
        "UserPermission",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("User.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("granted_by", sa.Integer(), sa.ForeignKey("User.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("user_id", "code", name="uq_user_permission"),
    )
    op.create_index("ix_UserPermission_user_id", "UserPermission", ["user_id"])
    op.create_index("ix_UserPermission_code", "UserPermission", ["code"])
    op.create_index("ix_UserPermission_expires_at", "UserPermission", ["expires_at"])


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "UserPermission"):
        op.drop_table("UserPermission")
