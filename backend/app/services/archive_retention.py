"""HHMS online/cold archive retention and tier promotion."""
from __future__ import annotations
import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.runtime_paths import archive_directory, cold_archive_directory
from app.config.settings import get_settings
from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.models.archive_manifest import ArchiveManifest
from app.services.operational_year import operational_year_service

@dataclass(frozen=True)
class ArchiveRetentionPlan:
    current_year: int
    online_years: int
    cold_years: int
    promote_to_cold: tuple[int, ...]
    retain_online: tuple[int, ...]
    retention_review: tuple[int, ...]
    invalid_or_future: tuple[int, ...]

class ArchiveRetentionService:
    async def plan(self, db: AsyncSession) -> ArchiveRetentionPlan:
        cfg = await operational_year_service.get_config(db)
        from datetime import date
        current_year = operational_year_service.current_year(date.today(), cfg)
        settings = get_settings()
        rows = list((await db.execute(select(ArchiveManifest).order_by(ArchiveManifest.archive_year))).scalars().all())
        promote=[]; online=[]; review=[]; invalid=[]
        for row in rows:
            age = current_year - row.archive_year
            if age < 1:
                invalid.append(row.archive_year)
            elif age <= settings.ONLINE_ARCHIVE_YEARS:
                online.append(row.archive_year)
            elif age <= settings.COLD_ARCHIVE_YEARS:
                promote.append(row.archive_year)
            else:
                review.append(row.archive_year)
        return ArchiveRetentionPlan(
            current_year=current_year,
            online_years=settings.ONLINE_ARCHIVE_YEARS,
            cold_years=settings.COLD_ARCHIVE_YEARS,
            promote_to_cold=tuple(promote),
            retain_online=tuple(online),
            retention_review=tuple(review),
            invalid_or_future=tuple(invalid),
        )

    async def promote_to_cold(self, db: AsyncSession, year: int) -> ArchiveManifest:
        plan = await self.plan(db)
        if year not in plan.promote_to_cold:
            if year in plan.retain_online:
                raise BusinessRuleException(f"Archive {year} is still within the online retention window.")
            if year in plan.retention_review:
                raise BusinessRuleException(f"Archive {year} is beyond the configured cold-retention window and requires policy review.")
            raise BusinessRuleException(f"Archive {year} is not eligible for cold promotion.")
        row = await db.scalar(select(ArchiveManifest).where(ArchiveManifest.archive_year == year))
        if row is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        if not row.verified:
            raise BusinessRuleException(f"Archive {year} is not verified and cannot be promoted.")
        source = Path(row.file_path)
        if not source.exists():
            raise ResourceNotFoundException(f"Archive file for {year} is missing from disk.")
        target_dir = cold_archive_directory() / str(year)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if target.exists():
            raise BusinessRuleException(f"Cold archive target already exists for {year}.")
        await asyncio.to_thread(shutil.move, str(source), str(target))
        row.storage_tier = "cold"
        row.file_path = str(target)
        await db.commit()
        await db.refresh(row)
        return row

    async def execute_eligible(self, db: AsyncSession) -> dict[str, object]:
        plan = await self.plan(db)
        promoted=[]
        for year in plan.promote_to_cold:
            row = await self.promote_to_cold(db, year)
            promoted.append(row.archive_year)
        return {"status":"completed","current_year":plan.current_year,"promoted_to_cold":promoted,"retained_online":list(plan.retain_online),"retention_review":list(plan.retention_review),"invalid_or_future":list(plan.invalid_or_future)}

archive_retention_service = ArchiveRetentionService()
__all__=["ArchiveRetentionPlan","ArchiveRetentionService","archive_retention_service"]
