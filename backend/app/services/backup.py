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


backup_service = BackupService()
__all__ = ["BackupService", "backup_service"]
