"""The institution's own registrations, and the practitioner's issuing authority.

A practitioner's number comes from a State Council in most states, not from NCH, so
``User.registration_number`` alone was a field that assumed an answer. It now has a
companion that records who issued it.

The institute registrations are a separate table because they are separate facts: one
BMW authorisation covers twelve doctors, and it expires on its own date.

Revision ID: 0042_institute_registrations
Revises: 0041_discharge_outcome
"""

from alembic import op
import sqlalchemy as sa

revision = "0042_institute_registrations"
down_revision = "0041_discharge_outcome"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    return any(
        row[1] == column for row in bind.exec_driver_sql(f'PRAGMA table_info("{table}")')
    )


def _has_table(bind, table: str) -> bool:
    return bind.exec_driver_sql(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
    ).fetchone() is not None


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_column(bind, "User", "registration_authority"):
        op.add_column("User", sa.Column("registration_authority", sa.String(40), nullable=True))

    if not _has_table(bind, "InstituteRegistration"):
        op.create_table(
            "InstituteRegistration",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kind", sa.String(40), nullable=False, unique=True),
            sa.Column("number", sa.String(80), nullable=False),
            sa.Column("authority", sa.String(160), nullable=True),
            sa.Column("issued_on", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("applies", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("recorded_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_InstituteRegistration_kind", "InstituteRegistration", ["kind"])
        op.create_index(
            "ix_InstituteRegistration_valid_until", "InstituteRegistration", ["valid_until"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "InstituteRegistration"):
        op.drop_table("InstituteRegistration")
    if _has_column(bind, "User", "registration_authority"):
        op.drop_column("User", "registration_authority")
