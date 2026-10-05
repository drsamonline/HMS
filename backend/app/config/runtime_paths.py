"""HHMS runtime filesystem paths for source and packaged deployments."""
from __future__ import annotations

import sys
from pathlib import Path


def application_root() -> Path:
    """Return the directory used as the HHMS application root.

    ``HHMS_APPLICATION_ROOT`` overrides the location for tests and for
    installations that keep their writable data directory outside the
    packaged application tree.
    """
    import os

    override = os.environ.get("HHMS_APPLICATION_ROOT")
    if override:
        return Path(override).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def data_directory() -> Path:
    """Return and create the writable HHMS data directory."""
    path = application_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_directory() -> Path:
    """Return and create the writable HHMS log directory."""
    path = data_directory() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def uploads_directory() -> Path:
    """Return and create the writable uploads directory."""
    path = data_directory() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def backups_directory() -> Path:
    """Return and create the writable backups directory."""
    path = data_directory() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_file_path() -> Path:
    """Return the optional server configuration file path."""
    return application_root() / ".env"


def database_path() -> Path:
    """Return the default SQLite database path."""
    return data_directory() / "hhms.sqlite3"


def archive_directory() -> Path:
    """Return the writable online archive directory."""
    path = data_directory() / "archive"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cold_archive_directory() -> Path:
    """Return the protected cold-archive directory."""
    path = data_directory() / "archive" / "cold"
    path.mkdir(parents=True, exist_ok=True)
    return path


def maintenance_directory() -> Path:
    """Return the writable maintenance workspace."""
    path = data_directory() / "maintenance"
    path.mkdir(parents=True, exist_ok=True)
    return path


def temporary_directory() -> Path:
    """Return the disposable HHMS temporary directory."""
    path = data_directory() / "tmp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def secret_key_path() -> Path:
    """Return the persisted local JWT secret path."""
    return data_directory() / "secret.key"

__all__ = [
    "application_root",
    "data_directory",
    "logs_directory",
    "uploads_directory",
    "backups_directory",
    "archive_directory",
    "cold_archive_directory",
    "maintenance_directory",
    "temporary_directory",
    "config_file_path",
    "database_path",
    "secret_key_path",
]


def server_identity_path() -> Path:
    """Return the persistent local server identity file path."""
    return data_directory() / "server_id"
