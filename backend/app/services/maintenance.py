"""HHMS safe runtime maintenance and database health."""
from __future__ import annotations
import asyncio, os, sqlite3, shutil
from datetime import datetime, timezone
from pathlib import Path
from app.config.runtime_paths import database_path, logs_directory, temporary_directory, backups_directory
from app.config.settings import get_settings
from app.services.backup import backup_service

class MaintenanceService:
    async def health(self) -> dict[str, object]:
        db_path=database_path(); disk=shutil.disk_usage(db_path.parent if db_path.parent.exists() else Path.cwd())
        out={"status":"healthy","database":{"exists":db_path.exists(),"size_bytes":db_path.stat().st_size if db_path.exists() else 0,"integrity":"unknown","journal_mode":"unknown","wal_bytes":0,"freelist_pages":0},"storage":{"free_bytes":disk.free,"total_bytes":disk.total},"backups":{"count":0,"latest":None},"archives":{"count":0},"retention":{"live_years":get_settings().LIVE_DATA_YEARS,"online_archive_years":get_settings().ONLINE_ARCHIVE_YEARS,"cold_archive_years":get_settings().COLD_ARCHIVE_YEARS}}
        if db_path.exists():
            def inspect():
                c=sqlite3.connect(db_path);
                try:
                    integrity=c.execute("PRAGMA integrity_check").fetchone()[0]
                    journal=c.execute("PRAGMA journal_mode").fetchone()[0]
                    freelist=c.execute("PRAGMA freelist_count").fetchone()[0]
                    return integrity,journal,freelist
                finally:c.close()
            integrity,journal,freelist=await asyncio.to_thread(inspect)
            out["database"]["integrity"]=integrity; out["database"]["journal_mode"]=journal; out["database"]["freelist_pages"]=freelist
            wal=Path(str(db_path)+"-wal"); out["database"]["wal_bytes"]=wal.stat().st_size if wal.exists() else 0
        backups=await backup_service.list_backups(); out["backups"]["count"]=len(backups); out["backups"]["latest"]=backups[0] if backups else None
        archive_root=database_path().parent/"archive"
        if archive_root.exists(): out["archives"]["count"]=sum(1 for _ in archive_root.glob("*/HHMS_*.sqlite3"))
        return out

    async def run_safe_maintenance(self) -> dict[str, object]:
        removed=0
        tmp=temporary_directory()
        for p in tmp.iterdir():
            try:
                if p.is_dir(): shutil.rmtree(p); removed+=1
                else: p.unlink(); removed+=1
            except OSError: pass
        logs=logs_directory(); now=datetime.now(timezone.utc).timestamp(); retention=get_settings().LOG_RETENTION_DAYS*86400
        for p in logs.glob("*.log.*"):
            try:
                if now-p.stat().st_mtime>retention: p.unlink(); removed+=1
            except OSError: pass
        db_path=database_path()
        if db_path.exists():
            def optimize():
                c=sqlite3.connect(db_path)
                try:
                    c.execute("PRAGMA wal_checkpoint(PASSIVE)")
                    c.execute("PRAGMA optimize")
                    c.commit()
                finally:c.close()
            await asyncio.to_thread(optimize)
        backup_created = None
        if get_settings().AUTO_BACKUP_ENABLED:
            backups = await backup_service.list_backups()
            latest = backups[0] if backups else None
            stale = latest is None
            if latest:
                latest_dt = latest.get("modified_at")
                stale = not latest_dt or (datetime.now(timezone.utc) - latest_dt).total_seconds() >= 86400
            if stale:
                backup_created = await backup_service.create_backup()
        return {"removed_runtime_items":removed,"backup_created":backup_created,"status":"completed","completed_at":datetime.now(timezone.utc)}

    async def vacuum(self) -> dict[str, object]:
        db_path=database_path()
        before=db_path.stat().st_size if db_path.exists() else 0
        def run():
            c=sqlite3.connect(db_path)
            try:c.execute("VACUUM"); c.commit()
            finally:c.close()
        await asyncio.to_thread(run)
        after=db_path.stat().st_size if db_path.exists() else 0
        return {"status":"completed","size_before":before,"size_after":after,"reclaimed_bytes":max(0,before-after),"completed_at":datetime.now(timezone.utc)}

maintenance_service=MaintenanceService()
__all__=["MaintenanceService","maintenance_service"]
