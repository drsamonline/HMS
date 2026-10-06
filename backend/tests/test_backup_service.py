from pathlib import Path


def test_backup_module_is_present() -> None:
    assert (Path(__file__).resolve().parents[2] / "backend/app/services/backup.py").exists()
    assert (Path(__file__).resolve().parents[2] / "backend/app/api/v1/endpoints/backups.py").exists()
