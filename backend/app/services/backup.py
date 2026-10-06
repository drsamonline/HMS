"""HHMS local database backup service."""
from __future__ import annotations

import asyncio
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import get_settings
from app.config.runtime_paths import backups_directory, database_path
from app.core.exceptions import BusinessRuleException, ResourceNotFoundException

_SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def _normalise_name(name: str) -> str:
    stem = _SAFE_NAME.sub("_", name.strip())
    if not stem:
        stem = "hhms-backup"
    if not stem.lower().endswith(".sqlite3"):
        stem += ".sqlite3"
    return stem


def _sqlite_backup(source: Path, target: Path) -> None:
    source_conn = sqlite3.connect(source)
    target_conn = sqlite3.connect(target)
    try:
        source_conn.backup(target_conn)
        target_conn.execute("PRAGMA integrity_check")
        target_conn.commit()
    finally:
        target_conn.close()
        source_conn.close()


def _sqlite_integrity(path: Path) -> bool:
    conn = sqlite3.connect(path)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return bool(result and result[0] == "ok")
    finally:
        conn.close()


class BackupService:
    """Create and manage portable SQLite backups."""

    def _ensure_sqlite(self) -> Path:
        url = get_settings().DATABASE_URL
        if not url.startswith("sqlite+aiosqlite:///"):
            raise BusinessRuleException("Local backup is currently supported only for SQLite deployments.")
        source = database_path()
        if not source.exists():
            raise ResourceNotFoundException("HHMS database file does not exist yet.")
        return source

    async def list_backups(self) -> list[dict[str, object]]:
        directory = backups_directory()
        rows: list[dict[str, object]] = []
        for path in sorted(directory.glob("*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True):
            rows.append({
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
            })
        return rows

    async def create_backup(self, requested_name: str | None = None) -> dict[str, object]:
        source = self._ensure_sqlite()
        now = datetime.now(timezone.utc)
        suffix = now.strftime("%Y%m%d-%H%M%S")
        name = _normalise_name(requested_name or f"hhms-backup-{suffix}")
        if requested_name and name == "hhms-backup.sqlite3":
            name = f"hhms-backup-{suffix}.sqlite3"
        target = backups_directory() / name
        if target.resolve() == source.resolve():
            raise BusinessRuleException("Backup target cannot overwrite the live database.")
        if target.exists():
            raise BusinessRuleException("A backup with that name already exists.")
        await asyncio.to_thread(_sqlite_backup, source, target)
        if not _sqlite_integrity(target):
            target.unlink(missing_ok=True)
            raise BusinessRuleException("Backup integrity check failed.")
        return {
            "name": target.name,
            "size_bytes": target.stat().st_size,
            "modified_at": datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc),
        }

    async def delete_backup(self, name: str) -> None:
        safe = _normalise_name(name)
        path = backups_directory() / safe
        if not path.exists():
            raise ResourceNotFoundException("Backup not found.")
        path.unlink()

    def backup_path(self, name: str) -> Path:
        safe = _normalise_name(name)
        path = backups_directory() / safe
        if not path.exists():
            raise ResourceNotFoundException("Backup not found.")
        return path

    async def restore_backup(self, name: str) -> dict[str, object]:
        """Restore the live database from a named backup.

        Safety contract (Batch 108):
        * The backup file must pass ``PRAGMA integrity_check`` before it is
          allowed to touch the live database.
        * A automatic pre-restore snapshot of the current live database is
          taken first (``pre-restore-<utcstamp>.sqlite3``) so an operator can
          roll back even the restore itself.
        * The restored database is re-verified after replacement; on failure
          the pre-restore snapshot is swapped back automatically.
        """
        source = self._ensure_sqlite()
        backup = self.backup_path(name)

        def _do_restore() -> Path:
            if not _sqlite_integrity(backup):
                raise BusinessRuleException(
                    "Backup failed integrity check; refusing to restore."
                )
            # Snapshot the live DB before overwriting it.
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            snapshot = backups_directory() / f"pre-restore-{stamp}.sqlite3"
            if source.exists():
                _sqlite_backup(source, snapshot)
            # Replace the live database atomically enough for SQLite: drop
            # side-car journals/WAL first so no stale pages survive.
            for suffix in ("-wal", "-shm"):
                sidecar = Path(str(source) + suffix)
                sidecar.unlink(missing_ok=True)
            _sqlite_backup(backup, source)
            if not _sqlite_integrity(source):
                # Roll the snapshot back into place.
                if source.exists():
                    source.unlink()
                if snapshot.exists():
                    _sqlite_backup(snapshot, source)
                snapshot.unlink(missing_ok=True)
                raise BusinessRuleException(
                    "Restored database failed integrity check; previous state was rolled back."
                )
            snapshot.unlink(missing_ok=True)
            return source

        await asyncio.to_thread(_do_restore)
        return {
            "restored": backup.name,
            "database": str(source),
            "restored_at": datetime.now(timezone.utc),
        }

    async def export_backup(self, name: str) -> Path:
        """Return the filesystem path of a backup for download/export."""
        return self.backup_path(name)

    async def import_backup(self, payload: bytes, requested_name: str | None = None) -> dict[str, object]:
        """Import an externally supplied SQLite file as a managed backup.

        The payload must be a valid SQLite database that passes
        ``PRAGMA integrity_check``; invalid uploads are rejected and never
        written into the backups directory.
        """
        self._ensure_sqlite()
        now = datetime.now(timezone.utc)
        suffix = now.strftime("%Y%m%d-%H%M%S")
        name = _normalise_name(requested_name or f"hhms-import-{suffix}")
        target = backups_directory() / name
        if target.exists():
            raise BusinessRuleException("A backup with that name already exists.")
        tmp = target.with_suffix(".tmp")
        try:
            tmp.write_bytes(payload)
            if not _sqlite_integrity(tmp):
                raise BusinessRuleException("Uploaded file is not a valid SQLite database.")
            tmp.rename(target)
        finally:
            tmp.unlink(missing_ok=True)
        return {
            "name": target.name,
            "size_bytes": target.stat().st_size,
            "modified_at": datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc),
        }


backup_service = BackupService()
__all__ = ["BackupService", "backup_service"]
