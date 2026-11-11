"""Add the first-run state table.

One row is created here with ``is_complete = 0``. An existing installation that
upgrades to this revision has already been set up by hand, so the migration marks
it complete when any user exists - otherwise every working hospital would be
greeted by a wizard asking it to name itself again.

Revision ID: 0036_setup_state
Revises: 0035_setting_value
"""

from alembic import op
import sqlalchemy as sa

revision = "0036_setup_state"
down_revision = "0035_setting_value"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    exists = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='SetupState'"
    ).fetchone()
    if not exists:
        op.create_table(
            "SetupState",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("is_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("code_hash", sa.String(64), nullable=True),
            sa.Column("code_issued_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("code_attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("steps_done", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    row = bind.exec_driver_sql("SELECT id FROM SetupState LIMIT 1").fetchone()
    if row:
        return

    users = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='User'"
    ).fetchone()
    already_used = False
    if users:
        already_used = bind.exec_driver_sql("SELECT 1 FROM \"User\" LIMIT 1").fetchone() is not None

    bind.exec_driver_sql(
        "INSERT INTO SetupState (is_complete, steps_done) VALUES (?, ?)",
        (
            1 if already_used else 0,
            "existing-installation" if already_used else None,
        ),
    )


def downgrade() -> None:
    op.drop_table("SetupState")
