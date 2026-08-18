"""HHMS annual archive management and historical case access."""
from __future__ import annotations
import asyncio, hashlib, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.runtime_paths import archive_directory, cold_archive_directory, database_path
from app.config.settings import get_settings
from app.core.exceptions import BusinessRuleException, ResourceNotFoundException
from app.models.archive_manifest import ArchiveManifest
from app.services.operational_year import operational_year_service

def _copy_sqlite(source: Path, target: Path) -> None:
    src=sqlite3.connect(source); dst=sqlite3.connect(target)
    try: src.backup(dst); dst.commit()
    finally: dst.close(); src.close()

def _integrity(path: Path) -> bool:
    con=sqlite3.connect(path)
    try: return con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally: con.close()

def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

class ArchiveManager:
    async def create_year_archive(self, db: AsyncSession, year: int, tier: str | None = None) -> ArchiveManifest:
        source=database_path()
        if not source.exists(): raise ResourceNotFoundException("HHMS database does not exist.")
        existing=await db.scalar(select(ArchiveManifest).where(ArchiveManifest.archive_year==year))
        if existing and existing.verified: return existing
        op_cfg = await operational_year_service.get_config(db)
        current_year = operational_year_service.current_year(datetime.now(timezone.utc).date(), op_cfg)
        if year >= current_year:
            raise BusinessRuleException("Only completed operational years can be archived.")
        age = current_year - year
        max_age = get_settings().COLD_ARCHIVE_YEARS
        if age > max_age:
            raise BusinessRuleException("Requested archive is outside the configured retention window.")
        chosen=tier or ("online" if age < get_settings().ONLINE_ARCHIVE_YEARS else "cold")
        if chosen == "online" and age >= get_settings().ONLINE_ARCHIVE_YEARS:
            raise BusinessRuleException("Archive age exceeds the online archive window.")
        base=cold_archive_directory() if chosen=="cold" else archive_directory()
        outdir=base/str(year); outdir.mkdir(parents=True,exist_ok=True)
        target=outdir/f"HHMS_{year}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.sqlite3"
        await asyncio.to_thread(_copy_sqlite, source, target)
        if not await asyncio.to_thread(_integrity,target):
            target.unlink(missing_ok=True); raise BusinessRuleException("Archive integrity check failed.")
        checksum=await asyncio.to_thread(_sha256,target)
        if existing:
            existing.storage_tier=chosen; existing.file_path=str(target); existing.checksum_sha256=checksum; existing.size_bytes=target.stat().st_size; existing.verified=True
            await db.commit(); await db.refresh(existing); return existing
        row=ArchiveManifest(archive_year=year,storage_tier=chosen,file_path=str(target),checksum_sha256=checksum,size_bytes=target.stat().st_size,verified=True)
        db.add(row); await db.commit(); await db.refresh(row); return row

    async def list_archives(self, db: AsyncSession) -> list[ArchiveManifest]:
        return list((await db.execute(select(ArchiveManifest).order_by(ArchiveManifest.archive_year.desc()))).scalars().all())


    async def read_case_records(self, db: AsyncSession, year: int, patient_id: int) -> list[dict[str, object]]:
        rows = await db.execute(select(ArchiveManifest).where(ArchiveManifest.archive_year == year))
        manifest = rows.scalar_one_or_none()
        if manifest is None:
            raise ResourceNotFoundException(f"Archive for {year} is not available.")
        path = self.archive_path(manifest)
        def query() -> list[dict[str, object]]:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                cur = con.execute(
                    "SELECT id, case_number, patient_id, case_year, case_status, storage_tier, is_current_year, renewed_from_case_id, created_at, updated_at "
                    "FROM CaseRecord WHERE patient_id = ? AND case_year = ? ORDER BY updated_at DESC, id DESC",
                    (patient_id, year),
                )
                return [dict(r) for r in cur.fetchall()]
            finally:
                con.close()
        return await asyncio.to_thread(query)

    def archive_path(self, manifest: ArchiveManifest) -> Path:
        p=Path(manifest.file_path)
        if not p.exists(): raise ResourceNotFoundException("Archive file is not available on disk.")
        return p

archive_manager=ArchiveManager()
__all__=["ArchiveManager","archive_manager"]
