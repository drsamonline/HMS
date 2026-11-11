"""The permission that lets an administrator tick a box for one person.

Migration 0032 seeds the catalogue and 0033 the role templates. Both have already run
on any database that exists, so a new code needs a migration of its own rather than an
edit to a file somebody has already applied.

Idempotent: it inserts the permission if it is missing and grants it to the all-access
roles, and does nothing on a second run.

Revision ID: 0044_roles_manage_permission
Revises: 0043_user_permissions
"""

from alembic import op
import sqlalchemy as sa

revision = "0044_roles_manage_permission"
down_revision = "0043_user_permissions"
branch_labels = None
depends_on = None

CODE = "roles.manage"
MODULE = "roles"
NAME = "Grant permissions to one person"
DESCRIPTION = (
    "Give an individual a permission their role does not provide, or take a manual "
    "grant back. Cannot grant anything the granter does not hold."
)

ALL_ACCESS_ROLES = ("administrator", "hospital administrator", "super administrator")


def upgrade() -> None:
    bind = op.get_bind()

    row = bind.execute(
        sa.text('SELECT id FROM "Permission" WHERE code = :code'), {"code": CODE}
    ).fetchone()

    if row is None:
        bind.execute(
            sa.text(
                'INSERT INTO "Permission" (name, code, module, description, is_active) '
                "VALUES (:name, :code, :module, :description, 1)"
            ),
            {"name": NAME, "code": CODE, "module": MODULE, "description": DESCRIPTION},
        )
        row = bind.execute(
            sa.text('SELECT id FROM "Permission" WHERE code = :code'), {"code": CODE}
        ).fetchone()

    permission_id = row[0]

    for role_name in ALL_ACCESS_ROLES:
        role = bind.execute(
            sa.text('SELECT id FROM "Role" WHERE lower(role_name) = :name'),
            {"name": role_name},
        ).fetchone()
        if role is None:
            continue
        exists = bind.execute(
            sa.text(
                'SELECT 1 FROM "RolePermission" WHERE role_id = :rid AND permission_id = :pid'
            ),
            {"rid": role[0], "pid": permission_id},
        ).fetchone()
        if exists is None:
            bind.execute(
                sa.text(
                    'INSERT INTO "RolePermission" (role_id, permission_id) '
                    "VALUES (:rid, :pid)"
                ),
                {"rid": role[0], "pid": permission_id},
            )


def downgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        sa.text('SELECT id FROM "Permission" WHERE code = :code'), {"code": CODE}
    ).fetchone()
    if row is None:
        return
    bind.execute(
        sa.text('DELETE FROM "RolePermission" WHERE permission_id = :pid'), {"pid": row[0]}
    )
    bind.execute(sa.text('DELETE FROM "Permission" WHERE id = :pid'), {"pid": row[0]})
