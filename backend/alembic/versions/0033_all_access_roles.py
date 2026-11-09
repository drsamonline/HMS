"""Grant every permission to the role names the client already treats as all-access.

The demo seed creates a role called `admin`; the catalogue in 0032 created
`administrator`. Both exist, both mean the same thing to a hospital, and only one
of them received grants - so an administrator logging in with the seeded `admin`
role would hold no permissions at all once the guard lands in B13.

The client has always treated four role names as all-access
(`frontend/js/rbac.js`). This migration makes the database say the same thing, so
the two layers cannot disagree about who is an administrator.

Revision ID: 0033_all_access_roles
Revises: 0032_permission_catalogue
"""

from alembic import op

revision = "0033_all_access_roles"
down_revision = "0032_permission_catalogue"
branch_labels = None
depends_on = None


ALL_ACCESS_ROLE_NAMES = (
    "admin",
    "administrator",
    "hospital administrator",
    "super administrator",
)


def upgrade() -> None:
    bind = op.get_bind()

    permission_ids = [
        row[0] for row in bind.exec_driver_sql("SELECT id FROM Permission").fetchall()
    ]
    if not permission_ids:
        return

    for role_name in ALL_ACCESS_ROLE_NAMES:
        role = bind.exec_driver_sql(
            "SELECT id FROM Role WHERE lower(role_name) = lower(?)", (role_name,)
        ).fetchone()
        if not role:
            continue
        role_id = role[0]
        for permission_id in permission_ids:
            exists = bind.exec_driver_sql(
                "SELECT id FROM RolePermission WHERE role_id = ? AND permission_id = ?",
                (role_id, permission_id),
            ).fetchone()
            if exists:
                continue
            bind.exec_driver_sql(
                "INSERT INTO RolePermission (role_id, permission_id) VALUES (?, ?)",
                (role_id, permission_id),
            )


def downgrade() -> None:
    # Nothing to undo that would be safe: the grants this made are
    # indistinguishable from grants an administrator made, and removing them
    # would lock people out of an installation that is running.
    pass
