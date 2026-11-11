"""HHMS audit-log query and export service.

Reading the trail is itself a privileged act, so the exports here record that they
happened. A reviewer who reads everything and exports nothing is invisible; a
reviewer who exports a copy of the trail leaves a row saying so.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import csv
import io
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


#: Column order for CSV and PDF, chosen to read like an account of events rather
#: than a table dump: when, who, what, to what, why.
EXPORT_COLUMNS = (
    "id",
    "action_timestamp",
    "actor_username",
    "actor_role",
    "activity",
    "outcome",
    "entity_name",
    "entity_id",
    "before_json",
    "after_json",
    "reason",
    "request_id",
    "ip_address",
)


class AuditLogService:
    def _filters(
        self,
        *,
        user_id: int | None,
        entity_name: str | None,
        activity: str | None,
        outcome: str | None,
        start_datetime: datetime | None,
        end_datetime: datetime | None,
    ) -> list:
        conditions = []
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        if entity_name:
            conditions.append(AuditLog.entity_name == entity_name)
        if activity:
            conditions.append(AuditLog.activity == activity)
        if outcome:
            conditions.append(AuditLog.outcome == outcome)
        if start_datetime is not None:
            conditions.append(AuditLog.action_timestamp >= start_datetime)
        if end_datetime is not None:
            conditions.append(AuditLog.action_timestamp <= end_datetime)
        return conditions

    async def list_recent(
        self, db: AsyncSession, *, user_id: int | None = None,
        entity_name: str | None = None, activity: str | None = None,
        outcome: str | None = None,
        start_datetime: datetime | None = None, end_datetime: datetime | None = None,
        skip: int = 0, limit: int = 100,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.action_timestamp.desc(), AuditLog.id.desc())
        for condition in self._filters(
            user_id=user_id, entity_name=entity_name, activity=activity,
            outcome=outcome, start_datetime=start_datetime, end_datetime=end_datetime,
        ):
            stmt = stmt.where(condition)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(
        self, db: AsyncSession, *, user_id: int | None = None,
        entity_name: str | None = None, activity: str | None = None,
        outcome: str | None = None,
        start_datetime: datetime | None = None, end_datetime: datetime | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(AuditLog)
        for condition in self._filters(
            user_id=user_id, entity_name=entity_name, activity=activity,
            outcome=outcome, start_datetime=start_datetime, end_datetime=end_datetime,
        ):
            stmt = stmt.where(condition)
        return int((await db.execute(stmt)).scalar_one())

    async def export_rows(
        self, db: AsyncSession, *, user_id: int | None = None,
        entity_name: str | None = None, activity: str | None = None,
        outcome: str | None = None,
        start_datetime: datetime | None = None, end_datetime: datetime | None = None,
        limit: int = 5000,
    ) -> list[AuditLog]:
        """The same filter as the review screen, oldest first.

        An export is an account of what happened, so it reads forwards. The
        review screen reads backwards because the newest event is the one being
        investigated.
        """

        stmt = select(AuditLog).order_by(AuditLog.id)
        for condition in self._filters(
            user_id=user_id, entity_name=entity_name, activity=activity,
            outcome=outcome, start_datetime=start_datetime, end_datetime=end_datetime,
        ):
            stmt = stmt.where(condition)
        result = await db.execute(stmt.limit(limit))
        return list(result.scalars().all())

    def to_csv(self, rows: list[AuditLog]) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(EXPORT_COLUMNS)
        for row in rows:
            writer.writerow([getattr(row, column) for column in EXPORT_COLUMNS])
        return buffer.getvalue().encode("utf-8")

    def to_pdf(self, rows: list[AuditLog], *, generated_at: datetime | None = None) -> bytes:
        """A printable account of the same rows the CSV carries."""

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        styles = getSampleStyleSheet()
        small = ParagraphStyle(
            "audit-small", parent=styles["Normal"], fontName="Helvetica",
            fontSize=7, leading=8.5,
        )
        heading = ParagraphStyle(
            "audit-heading", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=12, leading=15,
        )

        stamp = (generated_at or datetime.now()).strftime("%d/%m/%Y %H:%M")
        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer, pagesize=landscape(A4),
            leftMargin=12 * mm, rightMargin=12 * mm,
            topMargin=12 * mm, bottomMargin=12 * mm,
            title="HHMS audit trail export",
        )

        header = ["When", "Who", "Role", "Activity", "Outcome", "Entity", "Id", "Why"]
        data = [[Paragraph(f"<b>{cell}</b>", small) for cell in header]]
        for row in rows:
            data.append([
                Paragraph(str(row.action_timestamp or ""), small),
                Paragraph(str(row.actor_username or "-"), small),
                Paragraph(str(row.actor_role or "-"), small),
                Paragraph(str(row.activity), small),
                Paragraph(str(row.outcome), small),
                Paragraph(str(row.entity_name), small),
                Paragraph(str(row.entity_id if row.entity_id is not None else "-"), small),
                Paragraph(str(row.reason or "-"), small),
            ])

        table = Table(
            data,
            colWidths=[30 * mm, 24 * mm, 24 * mm, 34 * mm, 16 * mm, 24 * mm, 14 * mm, 90 * mm],
            repeatRows=1,
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B3A57")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#C3CDD6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        document.build([
            Paragraph("HHMS audit trail", heading),
            Paragraph(f"{len(rows)} entr{'y' if len(rows) == 1 else 'ies'} - generated {stamp}", small),
            Spacer(1, 6),
            table,
        ])
        return buffer.getvalue()


audit_log_service = AuditLogService()

__all__ = ["AuditLogService", "EXPORT_COLUMNS", "audit_log_service"]
