"""Split one reporting permission into three, by what each report answers.

Eighteen reports shared `reporting.read`, which six roles held - including laboratory
staff, who could therefore read the refund audit and the hospital's receivables. They
answer three different questions and now say so.

This migration creates the three codes and grants them to the roles the owner named.
`reporting.read` is left in place: it still guards the statistics module and the report
envelopes, and removing it would break routes that have nothing to do with this.

Revision ID: 0045_report_permissions
Revises: 0044_roles_manage_permission
"""

from alembic import op
import sqlalchemy as sa

revision = "0045_report_permissions"
down_revision = "0044_roles_manage_permission"
branch_labels = None
depends_on = None

NEW = (
    (
        "reports.operational",
        "View operational dashboards",
        "Bed occupancy, ward occupancy and the OPD queue - what the hospital is doing "
        "right now.",
    ),
    (
        "reports.clinical",
        "View clinical follow-through",
        "Due follow-ups, pending investigations and the discharge audit - what is "
        "outstanding for a patient.",
    ),
    (
        "reports.financial",
        "View financial reconciliation",
        "Receivables, refunds, overpayments, receipt continuity and settlement - does "
        "the money reconcile, and who authorised it.",
    ),
)

#: Who gets what. Decided by the owner, not inferred: the money is the money.
GRANTS = {
    "reports.operational": ("medical superintendent", "registration desk", "medical officer"),
    "reports.clinical": (
        "medical superintendent",
        "medical officer",
        "laboratory staff",
        "medical records",
    ),
    "reports.financial": ("medical superintendent", "auditor", "billing staff"),
}

ALL_ACCESS_ROLES = ("administrator", "hospital administrator", "super administrator")


def _permission_id(bind, code: str) -> int:
    row = bind.execute(
        sa.text('SELECT id FROM "Permission" WHERE code = :code'), {"code": code}
    ).fetchone()
    if row is not None:
        return row[0]
    bind.execute(
        sa.text(
            'INSERT INTO "Permission" (name, code, module, description, is_active) '
            "VALUES (:name, :code, 'reports', :description, 1)"
        ),
        {"name": code, "code": code, "description": ""},
    )
    return bind.execute(
        sa.text('SELECT id FROM "Permission" WHERE code = :code'), {"code": code}
    ).fetchone()[0]


def _grant(bind, role_name: str, permission_id: int) -> None:
    role = bind.execute(
        sa.text('SELECT id FROM "Role" WHERE lower(role_name) = :name'), {"name": role_name}
    ).fetchone()
    if role is None:
        return
    exists = bind.execute(
        sa.text('SELECT 1 FROM "RolePermission" WHERE role_id = :r AND permission_id = :p'),
        {"r": role[0], "p": permission_id},
    ).fetchone()
    if exists is None:
        bind.execute(
            sa.text('INSERT INTO "RolePermission" (role_id, permission_id) VALUES (:r, :p)'),
            {"r": role[0], "p": permission_id},
        )


def upgrade() -> None:
    bind = op.get_bind()

    for code, name, description in NEW:
        permission_id = _permission_id(bind, code)
        bind.execute(
            sa.text('UPDATE "Permission" SET name = :n, description = :d WHERE id = :i'),
            {"n": name, "d": description, "i": permission_id},
        )
        for role_name in GRANTS[code] + ALL_ACCESS_ROLES:
            _grant(bind, role_name, permission_id)


def downgrade() -> None:
    bind = op.get_bind()
    for code, _name, _description in NEW:
        row = bind.execute(
            sa.text('SELECT id FROM "Permission" WHERE code = :code'), {"code": code}
        ).fetchone()
        if row is None:
            continue
        bind.execute(
            sa.text('DELETE FROM "RolePermission" WHERE permission_id = :p'), {"p": row[0]}
        )
        bind.execute(sa.text('DELETE FROM "Permission" WHERE id = :p'), {"p": row[0]})
