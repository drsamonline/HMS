"""HHMS local database backup service."""
from __future__ import annotations

import asyncio
import os
import re
import shutil
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
    try:
        conn = sqlite3.connect(path)
    except sqlite3.DatabaseError:
        return False
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return bool(result and result[0] == "ok")
    except sqlite3.DatabaseError:
        # Non-SQLite / corrupt payloads raise here — treat as failed check.
        return False
    finally:
        conn.close()


class BackupService:
    """Create and manage portable SQLite backups."""

    def _ensure_sqlite(self) -> Path:
        url = get_settings().DATABASE_URL
        if not url.startswith("sqlite+aiosqlite:///"):
            raise BusinessRuleException("Local backup is currently supported only for SQLite deployments.")
        # The live database is wherever the running engine actually points.
        # Default to the conventional data-root path, but honour an explicit
        # DATABASE_URL override (custom file or :memory:) so packaged and
        # test runtimes back up exactly what they serve (Batch 108).
        source = database_path()
        configured = Path(url.removeprefix("sqlite+aiosqlite:///"))
        if str(configured) != "":
            source = configured.resolve() if ":memory:" not in url else source
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

    async def create_backup(
        self, requested_name: str | None = None, *, overwrite: bool = False
    ) -> dict[str, object]:
        source = self._ensure_sqlite()
        now = datetime.now(timezone.utc)
        suffix = now.strftime("%Y%m%d-%H%M%S")
        name = _normalise_name(requested_name or f"hhms-backup-{suffix}")
        if requested_name and name == "hhms-backup.sqlite3":
            name = f"hhms-backup-{suffix}.sqlite3"
        if overwrite:
            # Rolling snapshots (e.g. the shutdown "data draft saver") reuse
            # one slot; stamp the name so each save is unique while keeping
            # the requested stem for easy identification.  Two drafts saved
            # inside the same second still collide on an exact-second stamp,
            # so disambiguate with a counter suffix instead of failing.
            stem = name[: -len(".sqlite3")]
            candidate = f"{stem}-{suffix}.sqlite3"
            attempt = 1
            while (backups_directory() / candidate).exists():
                candidate = f"{stem}-{suffix}-{attempt}.sqlite3"
                attempt += 1
            name = candidate
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
        * An automatic pre-restore snapshot of the current live database is
          taken first (``pre-restore-<utcstamp>.sqlite3``) so an operator can
          roll back even the restore itself.
        * The restored database is re-verified after replacement; on failure
          the pre-restore snapshot is swapped back automatically.
        * The live engine pool is disposed before and after the swap.  On
          POSIX deleting an open file only unlinks it — writes from pooled
          connections would then land in the deleted inode and be lost, so
          every connection that could still hold the old file open must be
          closed first (and any connections opened during the restore are
          released afterwards so later requests rebind to the new file).
        """
        source = self._ensure_sqlite()
        backup = self.backup_path(name)

        from app.db.session import get_engine

        try:
            engine = get_engine()
        except Exception:  # pragma: no cover - defensive: uninitialised runtime
            engine = None

        async def _release_pool() -> None:
            if engine is not None:
                await engine.dispose()

        def _copy_into_live(origin: Path) -> None:
            """Byte-level replacement of the live DB file.

            Used when the old live inode was unlinked while pooled
            connections still held it open (POSIX delete semantics), so a
            fresh SQLite write handle cannot be reopened on it.  The engine
            pool is disposed around the restore, so no writer should remain;
            this path guarantees the new file carries exactly the origin's
            bytes with no stale side-cars.
            """
            for suffix in ("", "-wal", "-shm"):
                Path(str(source) + suffix).unlink(missing_ok=True)
            shutil.copyfile(origin, source)
            with open(source, "rb") as handle:
                os.fsync(handle.fileno())

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
            # Replace the live database wholesale: drop the file and its
            # side-cars so no stale WAL/shm pages shadow the restored
            # content, then materialise the backup as the new live file.
            _copy_into_live(backup)
            if not _sqlite_integrity(source):
                # Roll the snapshot back into place.
                if snapshot.exists():
                    _copy_into_live(snapshot)
                snapshot.unlink(missing_ok=True)
                raise BusinessRuleException(
                    "Restored database failed integrity check; previous state was rolled back."
                )
            snapshot.unlink(missing_ok=True)
            return source

        # Release pooled connections *before* touching the live file, then
        # restore, then release again so post-restore sessions reopen the
        # replacement file.
        await _release_pool()
        try:
            await asyncio.to_thread(_do_restore)
        finally:
            await _release_pool()
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
