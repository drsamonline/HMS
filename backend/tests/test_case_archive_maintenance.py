from datetime import datetime, timezone
from pathlib import Path

def test_case_lifecycle_fields_are_declared():
    from app.models.case_record import CaseRecord
    assert hasattr(CaseRecord,"case_family_id")
    assert hasattr(CaseRecord,"case_year")
    assert hasattr(CaseRecord,"storage_tier")
    assert hasattr(CaseRecord,"is_current_year")

def test_runtime_archive_paths(tmp_path, monkeypatch):
    from app.config import runtime_paths
    monkeypatch.setattr(runtime_paths,"data_directory",lambda: tmp_path)
    assert runtime_paths.archive_directory().name == "archive"
    assert runtime_paths.cold_archive_directory().name == "cold"
    assert runtime_paths.maintenance_directory().name == "maintenance"


def test_maintenance_policy_defaults():
    from app.config.settings import get_settings
    settings=get_settings()
    assert settings.LIVE_DATA_YEARS == 1
    assert settings.ONLINE_ARCHIVE_YEARS == 5
    assert settings.COLD_ARCHIVE_YEARS == 10


def test_archive_manifest_fields():
    from app.models.archive_manifest import ArchiveManifest
    assert hasattr(ArchiveManifest,"archive_year")
    assert hasattr(ArchiveManifest,"checksum_sha256")
    assert hasattr(ArchiveManifest,"verified")
