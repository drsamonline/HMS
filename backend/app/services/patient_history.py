"""Unified patient history across live records and selected operational-year archives."""
from __future__ import annotations

import asyncio
import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.archive_manifest import ArchiveManifest
from app.models.case_record import CaseRecord
from app.services.archive_manager import archive_manager
from app.services.operational_year import operational_year_service


class PatientHistoryService:
    async def available_archives(self, db: AsyncSession) -> list[dict[str, Any]]:
        cfg = await operational_year_service.get_config(db)
        current_year = operational_year_service.current_year(date.today(), cfg)
        rows = list((await db.execute(
            select(ArchiveManifest).where(ArchiveManifest.verified.is_(True)).order_by(ArchiveManifest.archive_year.desc())
        )).scalars().all())
        return [
            {
                "year": row.archive_year,
                "storage_tier": row.storage_tier,
                "verified": row.verified,
                "is_current": row.archive_year == current_year,
            }
            for row in rows
            if row.archive_year != current_year
        ]

    async def live_cases(self, db: AsyncSession, patient_id: int) -> list[dict[str, Any]]:
        rows = list((await db.execute(
            select(CaseRecord).where(CaseRecord.patient_id == patient_id).order_by(CaseRecord.updated_at.desc(), CaseRecord.id.desc())
        )).scalars().all())
        return [
            {
                "id": row.id,
                "case_number": row.case_number,
                "patient_id": row.patient_id,
                "case_year": row.case_year,
                "case_status": row.case_status,
                "storage_tier": row.storage_tier,
                "is_current_year": row.is_current_year,
                "case_family_id": row.case_family_id,
                "renewed_from_case_id": row.renewed_from_case_id,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "source": "live",
                "read_only": False,
            }
            for row in rows
        ]

    async def archived_cases(self, db: AsyncSession, patient_id: int, years: list[int]) -> list[dict[str, Any]]:
        selected = {int(year) for year in years}
        if not selected:
            return []
        manifests = list((await db.execute(
            select(ArchiveManifest).where(
                ArchiveManifest.archive_year.in_(selected),
                ArchiveManifest.verified.is_(True),
            )
        )).scalars().all())
        result: list[dict[str, Any]] = []
        for manifest in manifests:
            rows = await archive_manager.read_case_records(db, manifest.archive_year, patient_id)
            for row in rows:
                row["source"] = "archive"
                row["storage_tier"] = manifest.storage_tier
                row["read_only"] = True
                result.append(row)
        return result

    async def archived_events(self, db: AsyncSession, patient_id: int, year: int) -> list[dict[str, Any]]:
        manifests = list((await db.execute(
            select(ArchiveManifest).where(
                ArchiveManifest.archive_year == year,
                ArchiveManifest.verified.is_(True),
            )
        )).scalars().all())
        if not manifests:
            return []
        manifest = manifests[0]
        path = archive_manager.archive_path(manifest)
        config = await operational_year_service.get_config(db)
        start_dt, end_dt = operational_year_service.bounds_for_year(year, config)
        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()

        def query() -> list[dict[str, Any]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                events: list[dict[str, Any]] = []

                queries = []
                if "Visit" in tables:
                    queries.append((
                        """SELECT visit_datetime AS event_datetime, 'OPD Visit' AS event_type,
                                  COALESCE(visit_number, 'OPD Visit') AS title,
                                  COALESCE(visit_type, 'OPD') || ' · ' || COALESCE(consultation_status, '—') AS meta,
                                  COALESCE(chief_complaint, '') AS detail
                           FROM "Visit"
                          WHERE patient_id = ? AND visit_datetime >= ? AND visit_datetime < ?""",
                        (patient_id, start_iso, end_iso),
                    ))
                if "Admission" in tables:
                    queries.append((
                        """SELECT admission_datetime AS event_datetime, 'IPD Admission' AS event_type,
                                  COALESCE(admission_number, 'Admission') AS title,
                                  COALESCE(admission_status, '—') || ' · Bed ' || COALESCE(CAST(bed_id AS TEXT), '—') AS meta,
                                  COALESCE(admission_reason, '') AS detail
                           FROM "Admission"
                          WHERE patient_id = ? AND admission_datetime >= ? AND admission_datetime < ?""",
                        (patient_id, start_iso, end_iso),
                    ))
                if "Investigation" in tables:
                    queries.append((
                        """SELECT requested_datetime AS event_datetime, 'Investigation' AS event_type,
                                  COALESCE(investigation_number, investigation_name, 'Investigation') AS title,
                                  COALESCE(investigation_status, '—') || ' · ' || COALESCE(fulfillment_mode, '—') AS meta,
                                  COALESCE(remarks, '') AS detail
                           FROM "Investigation"
                          WHERE patient_id = ? AND requested_datetime >= ? AND requested_datetime < ?""",
                        (patient_id, start_iso, end_iso),
                    ))
                if "Invoice" in tables:
                    queries.append((
                        """SELECT invoice_date AS event_datetime, 'Billing' AS event_type,
                                  COALESCE(invoice_number, 'Invoice') AS title,
                                  COALESCE(payment_status, '—') || ' · Total ' || COALESCE(CAST(total_amount AS TEXT), '—') AS meta,
                                  COALESCE(remarks, '') AS detail
                           FROM "Invoice"
                          WHERE patient_id = ? AND invoice_date >= ? AND invoice_date < ?""",
                        (patient_id, start_iso, end_iso),
                    ))
                if "PatientFile" in tables:
                    queries.append((
                        """SELECT created_at AS event_datetime, 'MRD' AS event_type,
                                  COALESCE(file_no, 'Patient File') AS title,
                                  COALESCE(file_type, '—') || ' · ' || COALESCE(status, '—') AS meta,
                                  COALESCE(location, '') AS detail
                           FROM "PatientFile"
                          WHERE patient_id = ? AND created_at >= ? AND created_at < ?""",
                        (patient_id, start_iso, end_iso),
                    ))
                if "Prescription" in tables and "Visit" in tables:
                    queries.append((
                        """SELECT p.prescription_datetime AS event_datetime, 'Prescription' AS event_type,
                                  COALESCE(p.prescription_number, 'Prescription') AS title,
                                  'Prescription' AS meta,
                                  COALESCE(p.diagnosis, '') AS detail
                           FROM "Prescription" p
                           JOIN "Visit" v ON v.id = p.visit_id
                          WHERE v.patient_id = ? AND p.prescription_datetime >= ? AND p.prescription_datetime < ?""",
                        (patient_id, start_iso, end_iso),
                    ))
                if "Diagnosis" in tables:
                    queries.append((
                        """SELECT created_at AS event_datetime, 'Diagnosis' AS event_type,
                                  COALESCE(diagnosis_name, 'Diagnosis') AS title,
                                  COALESCE(diagnosis_type, '—') || CASE WHEN is_primary = 1 THEN ' · Primary' ELSE '' END AS meta,
                                  COALESCE(icd11_code, '') AS detail
                           FROM "Diagnosis"
                          WHERE patient_id = ? AND created_at >= ? AND created_at < ?""",
                        (patient_id, start_iso, end_iso),
                    ))
                if "FollowUp" in tables:
                    queries.append((
                        """SELECT followup_datetime AS event_datetime, 'Follow-up' AS event_type,
                                  'Follow-up' AS title,
                                  COALESCE(remedy_response, '—') || ' · ' || COALESCE(decision, '—') AS meta,
                                  COALESCE(clinical_assessment, '') AS detail
                           FROM "FollowUp"
                          WHERE patient_id = ? AND followup_datetime >= ? AND followup_datetime < ?""",
                        (patient_id, start_iso, end_iso),
                    ))
                if "CaseRecord" in tables:
                    queries.append((
                        """SELECT updated_at AS event_datetime, 'Historical Case' AS event_type,
                                  COALESCE(case_number, 'Case') AS title,
                                  'Year ' || CAST(case_year AS TEXT) || ' · ' || COALESCE(storage_tier, 'archive') AS meta,
                                  COALESCE(case_status, '') AS detail
                           FROM "CaseRecord"
                          WHERE patient_id = ? AND case_year = ?""",
                        (patient_id, year),
                    ))

                for sql, params in queries:
                    events.extend(dict(row) for row in con.execute(sql, params).fetchall())
                return events
            finally:
                con.close()

        rows = await asyncio.to_thread(query)
        for row in rows:
            row["source"] = "archive"
            row["storage_tier"] = manifest.storage_tier
            row["read_only"] = True
            row["year"] = year
        return rows

    async def unified(self, db: AsyncSession, patient_id: int, years: list[int] | None = None) -> dict[str, Any]:
        archives = await self.available_archives(db)
        live = await self.live_cases(db, patient_id)
        selected = sorted({int(year) for year in (years or [])})
        archived = await self.archived_cases(db, patient_id, selected)
        historical_events: list[dict[str, Any]] = []
        for year in selected:
            historical_events.extend(await self.archived_events(db, patient_id, year))
        return {
            "patient_id": patient_id,
            "current_operational_year": operational_year_service.current_year(date.today(), await operational_year_service.get_config(db)),
            "available_archives": archives,
            "selected_archive_years": selected,
            "cases": live + archived,
            "historical_events": historical_events,
        }


patient_history_service = PatientHistoryService()
__all__ = ["PatientHistoryService", "patient_history_service"]
