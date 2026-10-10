"""Seed operational-year configuration defaults."""
from alembic import op
import sqlalchemy as sa

revision = "0016_operational_year_settings"
down_revision = "0015_case_year_archive_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = sa.table(
        "SystemSetting",
        sa.column("setting_key", sa.String()),
        sa.column("setting_value", sa.String()),
        sa.column("setting_type", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_editable", sa.Boolean()),
    )
    conn = op.get_bind()
    existing = {r[0] for r in conn.execute(sa.text('SELECT setting_key FROM "SystemSetting"')).fetchall()}
    rows = [
        {"setting_key":"operational_year_basis","setting_value":"calendar","setting_type":"string","description":"Calendar or financial operational year basis.","is_editable":True},
        {"setting_key":"financial_year_start_month","setting_value":"4","setting_type":"integer","description":"Financial year start month (1-12).","is_editable":True},
        {"setting_key":"financial_year_start_day","setting_value":"1","setting_type":"integer","description":"Financial year start day (1-31).","is_editable":True},
    ]
    for row in rows:
        if row["setting_key"] not in existing:
            conn.execute(table.insert().values(**row))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text('DELETE FROM "SystemSetting" WHERE setting_key IN (\'operational_year_basis\',\'financial_year_start_month\',\'financial_year_start_day\')'))
