"""Make the audit trail append-only, and make a silent edit detectable.

Two controls, because they answer different threats.

**Triggers** stop the ordinary case: a developer, a support session or a script
issuing DELETE or UPDATE against AuditLog. They fail loudly, at the database, for
every client - including raw SQL, which an application-level guard would miss.

**A hash chain** answers the case the triggers cannot: someone with file-level
access to the SQLite database, or a DBA who drops the trigger first. Each row
carries a SHA-256 over its own evidence plus the previous row's hash, so removing
a row breaks the link after it and editing a field breaks the row's own hash. A
verifier walks the chain and reports the first id that does not reconcile.

The chain is not tamper-proof against an attacker who recomputes every subsequent
hash. It is tamper-*evident*, and the difference matters: it turns a silent edit
into a detectable one, which is what an auditor needs. Storing the head hash
somewhere outside the database - a signed daily digest emailed to the medical
superintendent - is the next step, and belongs to the NABH module rather than
here.

Existing rows are backfilled in id order so the chain is complete from row one.

Revision ID: 0031_audit_log_hash_chain
Revises: 0030_audit_log_evidence_columns
"""

from alembic import op
import hashlib
import json
import sqlalchemy as sa
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

revision = "0031_audit_log_hash_chain"
down_revision = "0030_audit_log_evidence_columns"
branch_labels = None
depends_on = None


#: Fields covered by the hash. Deliberately excludes ``id``: the hash has to be
#: computable before the row is inserted, and the id is assigned by the insert.
HASHED_FIELDS = (
    "user_id",
    "actor_username",
    "actor_role",
    "activity",
    "outcome",
    "entity_name",
    "entity_id",
    "before_json",
    "after_json",
    "reason",
    "action_timestamp",
    "request_id",
    "ip_address",
    "user_agent",
    "remarks",
)


def _canonical(value):
    """Must match ``app.services.audit._jsonable`` exactly.

    Migrations are frozen in time and must not import application code that will
    change under them, so this is a deliberate duplicate. If the two ever drift,
    the verifier reports every backfilled row as edited - loudly, which is the
    correct failure mode for a chain.
    """

    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.strftime("%Y-%m-%dT%H:%M:%S.%f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def compute_hash(row: dict, prev_hash: str | None) -> str:
    payload = {field: _canonical(row.get(field)) for field in HASHED_FIELDS}
    payload["prev_hash"] = prev_hash
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _columns(bind, table: str) -> set[str]:
    return {row[1] for row in bind.exec_driver_sql(f"PRAGMA table_info({table})")}


def upgrade() -> None:
    bind = op.get_bind()
    existing = _columns(bind, "AuditLog")

    if "prev_hash" not in existing:
        op.add_column("AuditLog", sa.Column("prev_hash", sa.String(length=64), nullable=True))
    if "row_hash" not in existing:
        op.add_column("AuditLog", sa.Column("row_hash", sa.String(length=64), nullable=True))

    bind.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_audit_log_row_hash ON AuditLog (row_hash)"
    )

    # Backfill in id order so a database that already holds rows gets a chain
    # rather than a permanent gap at the head.
    rows = bind.exec_driver_sql(
        "SELECT id, " + ", ".join(HASHED_FIELDS) + " FROM AuditLog ORDER BY id"
    ).mappings().all()

    prev = None
    for row in rows:
        value = compute_hash(dict(row), prev)
        bind.exec_driver_sql(
            "UPDATE AuditLog SET prev_hash = ?, row_hash = ? WHERE id = ?",
            (prev, value, row["id"]),
        )
        prev = value

    # Triggers: the ordinary case, stopped at the database for every client.
    bind.exec_driver_sql(
        """
        CREATE TRIGGER IF NOT EXISTS trg_audit_log_no_delete
        BEFORE DELETE ON AuditLog
        BEGIN
            SELECT RAISE(ABORT, 'AuditLog is append-only: rows cannot be deleted.');
        END
        """
    )
    bind.exec_driver_sql(
        """
        CREATE TRIGGER IF NOT EXISTS trg_audit_log_no_update
        BEFORE UPDATE ON AuditLog
        BEGIN
            SELECT RAISE(ABORT, 'AuditLog is append-only: rows cannot be modified.');
        END
        """
    )


def downgrade() -> None:
    bind = op.get_bind()

    bind.exec_driver_sql("DROP TRIGGER IF EXISTS trg_audit_log_no_update")
    bind.exec_driver_sql("DROP TRIGGER IF EXISTS trg_audit_log_no_delete")
    bind.exec_driver_sql("DROP INDEX IF EXISTS ix_audit_log_row_hash")

    existing = _columns(bind, "AuditLog")
    for name in ("row_hash", "prev_hash"):
        if name in existing:
            with op.batch_alter_table("AuditLog") as batch_op:
                batch_op.drop_column(name)
