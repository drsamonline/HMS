"""Align RBAC tables with existing integer User/Role schema.
Revision ID: 0008_rbac_consistency
Revises: 0007_clinical_activity_integration
"""
from alembic import op
import sqlalchemy as sa
revision="0008_rbac_consistency"; down_revision="0007_clinical_activity_integration"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("Permission",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("name",sa.String(100),nullable=False),sa.Column("code",sa.String(100),nullable=False),sa.Column("module",sa.String(100),nullable=False),sa.Column("description",sa.Text(),nullable=True),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.text("true")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")),sa.UniqueConstraint("name",name="uq_permission_name"),sa.UniqueConstraint("code",name="uq_permission_code"))
    op.create_table("UserRole",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),nullable=False),sa.Column("role_id",sa.Integer(),nullable=False),sa.Column("assigned_by",sa.Integer(),nullable=True),sa.ForeignKeyConstraint(["user_id"],["User.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["role_id"],["Role.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["assigned_by"],["User.id"],ondelete="SET NULL"),sa.UniqueConstraint("user_id","role_id",name="uq_user_role_user_role"))
    op.create_table("RolePermission",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("role_id",sa.Integer(),nullable=False),sa.Column("permission_id",sa.Integer(),nullable=False),sa.Column("assigned_by",sa.Integer(),nullable=True),sa.ForeignKeyConstraint(["role_id"],["Role.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["permission_id"],["Permission.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["assigned_by"],["User.id"],ondelete="SET NULL"),sa.UniqueConstraint("role_id","permission_id",name="uq_role_permission_role_permission"))
def downgrade():
    op.drop_table("RolePermission"); op.drop_table("UserRole"); op.drop_table("Permission")
