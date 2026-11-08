"""Add the evidence columns an audit row needs to be worth anything.

The AuditLog table shipped with who, what and when. It had no before-and-after,
no reason, no request correlation and no outcome, and nothing in the application
ever wrote a row. This migration adds the columns; build plan B08 adds the write
path and B09 wires it into every service.

Three columns the earlier plan named are deliberately **not** added:

* ``actor_id`` - ``user_id`` already is the actor. Two columns meaning the same
  thing become two sources of truth.
* ``action`` - ``activity`` already is the action.
* ``occurred_at`` - ``action_timestamp`` already is the time.

``user_id`` becomes nullable so a failed authentication for a username that does
not exist can be recorded at all; ``actor_username`` carries the name as it stood
at the time, because an audit entry must still name a person after the user row
has been renamed or deactivated.

The upgrade is guarded on ``PRAGMA table_info`` because the test suite builds its
databases from ``Base.metadata.create_all``, which already contains these
columns; an unguarded ``ADD COLUMN`` would fail there and hide the real problem.

Revision ID: 0030_audit_log_evidence_columns
Revises: 0029_department_service_is_active
"""

from alembic import op
import sqlalchemy as sa

revision = "0030_audit_log_evidence_columns"
down_revision = "0029_department_service_is_active"
branch_labels = None
depends_on = None


ADDED_COLUMNS = (
    ("actor_username", sa.String(length=120)),
    ("actor_role", sa.String(length=200)),
    ("outcome", sa.String(length=20)),
    ("before_json", sa.Text()),
    ("after_json", sa.Text()),
    ("reason", sa.Text()),
    ("request_id", sa.String(length=64)),
    ("user_agent", sa.String(length=255)),
)


def _columns(bind, table: str) -> set[str]:
    return {row[1] for row in bind.exec_driver_sql(f"PRAGMA table_info({table})")}


def upgrade() -> None:
    bind = op.get_bind()
    existing = _columns(bind, "AuditLog")

    for name, column_type in ADDED_COLUMNS:
        if name in existing:
            continue
        if name == "outcome":
            # Every row has an outcome, so the column carries a default rather
            # than staying null on rows written before B08 existed. The default
            # must match the model's ``server_default`` or the two disagree
            # about what an insert with no outcome means.
            op.add_column(
                "AuditLog",
                sa.Column(
                    name,
                    column_type,
                    nullable=True,
                    server_default=sa.text("'success'"),
                ),
            )
            continue
        op.add_column("AuditLog", sa.Column(name, column_type, nullable=True))

    # Backfill any row that predates the default.
    if "outcome" in _columns(bind, "AuditLog"):
        bind.exec_driver_sql(
            "UPDATE AuditLog SET outcome = 'success' WHERE outcome IS NULL"
        )

    with op.batch_alter_table("AuditLog") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=True,
        )

    # Indexes for the two questions an assessor actually asks: "everything that
    # happened to this record" and "everything this person did, over time".
    bind.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_audit_log_entity "
        "ON AuditLog (entity_name, entity_id)"
    )
    bind.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_audit_log_actor_time "
        "ON AuditLog (user_id, action_timestamp)"
    )
    bind.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_audit_log_request_id "
        "ON AuditLog (request_id)"
    )


def downgrade() -> None:
    bind = op.get_bind()

    for index_name in (
        "ix_audit_log_request_id",
        "ix_audit_log_actor_time",
        "ix_audit_log_entity",
    ):
        bind.exec_driver_sql(f"DROP INDEX IF EXISTS {index_name}")

    existing = _columns(bind, "AuditLog")
    for name, _column_type in ADDED_COLUMNS:
        if name in existing:
            with op.batch_alter_table("AuditLog") as batch_op:
                batch_op.drop_column(name)

    # Restoring NOT NULL is only safe when no null actor rows were written while
    # the column was nullable. Leaving it nullable is the honest outcome; a
    # downgrade that fails halfway is worse than one that leaves a looser
    # constraint and says so.
    orphaned = bind.exec_driver_sql(
        "SELECT COUNT(*) FROM AuditLog WHERE user_id IS NULL"
    ).fetchone()[0]
    if orphaned == 0:
        with op.batch_alter_table("AuditLog") as batch_op:
            batch_op.alter_column(
                "user_id",
                existing_type=sa.Integer(),
                nullable=False,
            )
