"""
HHMS AuditLog ORM Model.

Implements the AuditLog table defined in DATABASE_SCHEMA.md.

An audit row has to answer four questions before it is worth anything in a
dispute, an accreditation assessment or a financial audit: **who** acted, **what**
they did, **what the record said before and after**, and **why**. The original
table answered only the first two, and only in principle - nothing ever wrote a
row. This model carries the evidence columns the audit trail needs.

Design notes
------------
``user_id`` is the actor. There is deliberately no second ``actor_id`` column:
two columns meaning the same thing become two sources of truth, and the one that
drifts is always the one somebody forgot to populate.

``activity`` is the action and ``action_timestamp`` is the time, for the same
reason. The columns added here are the ones that did not exist in any form.

``user_id`` is nullable so that a failed authentication for a username that does
not exist can still be recorded. ``actor_username`` is denormalised on purpose:
an audit entry must still name the person after the user row is renamed or
deactivated, and a foreign key cannot promise that.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """
    Append-only record of who did what, to which record, and why.

    Rows are never updated or deleted. Withdrawal of a decision is expressed by
    a new row, not by editing the old one - see build plan B10 for the database
    guard and the hash chain that make that structural rather than a convention.
    """

    __tablename__ = "AuditLog"

    __table_args__ = (
        Index(
            "ix_audit_log_entity",
            "entity_name",
            "entity_id",
        ),
        Index(
            "ix_audit_log_actor_time",
            "user_id",
            "action_timestamp",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # ---------------------------------------------------------------- actor
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "User.id",
            name="fk_audit_log_user",
        ),
        nullable=True,
        index=True,
    )

    actor_username: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        doc=(
            "Username as it stood when the action happened. Denormalised so the "
            "entry survives a rename or a deactivation."
        ),
    )

    actor_role: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        doc=(
            "Comma-joined role names held at the time. Denormalised for the same "
            "reason: an assessor asks what authority the actor had, not what "
            "authority their account has today."
        ),
    )

    # --------------------------------------------------------------- action
    activity: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    outcome: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="success",
        server_default="success",
        doc="success, failure or denied.",
    )

    # --------------------------------------------------------------- entity
    entity_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ------------------------------------------------------------- evidence
    before_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Changed fields as they were before the action, as JSON.",
    )

    after_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="The same fields as they were after the action, as JSON.",
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc=(
            "Why the actor made the change. Required for anything an assessor "
            "would question: a voided invoice, a changed prescription, a "
            "withdrawn consent."
        ),
    )

    # -------------------------------------------------------------- context
    action_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="Ties every row written during one HTTP request together.",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------- integrity
    prev_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc=(
            "row_hash of the previous row in the chain. A row whose prev_hash "
            "does not match its predecessor is a row that was removed or "
            "reordered."
        ),
    )

    row_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc=(
            "SHA-256 over this row's evidence and its prev_hash. Changing any "
            "field changes this value, which is how a silent edit is found."
        ),
    )


__all__ = [
    "AuditLog",
]
