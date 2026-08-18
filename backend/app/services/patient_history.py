"""Unified patient history across live and explicitly selected archives."""
from __future__ import annotations

import asyncio
import sqlite3
from datetime import date
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

    async def unified(self, db: AsyncSession, patient_id: int, years: list[int] | None = None) -> dict[str, Any]:
        archives = await self.available_archives(db)
        live = await self.live_cases(db, patient_id)
        archived = await self.archived_cases(db, patient_id, years or [])
        return {
            "patient_id": patient_id,
            "current_operational_year": operational_year_service.current_year(date.today(), await operational_year_service.get_config(db)),
            "available_archives": archives,
            "selected_archive_years": sorted({int(year) for year in (years or [])}),
            "cases": live + archived,
        }


patient_history_service = PatientHistoryService()
__all__ = ["PatientHistoryService", "patient_history_service"]
