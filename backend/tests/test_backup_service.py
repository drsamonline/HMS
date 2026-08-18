from pathlib import Path


def test_backup_module_is_present() -> None:
    assert Path("backend/app/services/backup.py").exists()
    assert Path("backend/app/api/v1/endpoints/backups.py").exists()
