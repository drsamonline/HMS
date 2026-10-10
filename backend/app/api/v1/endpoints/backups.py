"""Administrative database backup endpoints."""
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.backup import BackupCreate, BackupRead, BackupRestoreResult
from app.services.administration import _require_admin
from app.services.backup import backup_service

router = APIRouter(prefix="/maintenance/backups", tags=["Maintenance"])

def actor_id(current_user: CurrentUserDependency) -> int:
    return int(str(current_user["sub"]))

@router.get("", response_model=list[BackupRead])
async def list_backups(db: DatabaseSession, current_user: CurrentUserDependency) -> list[dict]:
    await _require_admin(db, actor_id(current_user))
    return await backup_service.list_backups()

@router.post("", response_model=BackupRead, status_code=status.HTTP_201_CREATED)
async def create_backup(data: BackupCreate, db: DatabaseSession, current_user: CurrentUserDependency) -> dict:
    await _require_admin(db, actor_id(current_user))
    return await backup_service.create_backup(data.name)

@router.post("/import", response_model=BackupRead, status_code=status.HTTP_201_CREATED)
async def import_backup(
    db: DatabaseSession,
    current_user: CurrentUserDependency,
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
) -> dict:
    """Upload an external SQLite file and register it as a managed backup."""
    await _require_admin(db, actor_id(current_user))
    payload = await file.read()
    return await backup_service.import_backup(payload, name)

@router.get("/{name}/download", response_class=FileResponse)
async def download_backup(name: str, db: DatabaseSession, current_user: CurrentUserDependency) -> FileResponse:
    await _require_admin(db, actor_id(current_user))
    path = backup_service.backup_path(name)
    return FileResponse(path=path, filename=path.name, media_type="application/octet-stream")

@router.post("/{name}/restore", response_model=BackupRestoreResult)
async def restore_backup(name: str, db: DatabaseSession, current_user: CurrentUserDependency) -> dict:
    """Restore the live database from a named backup (admin only).

    A pre-restore snapshot is taken automatically; integrity of both the
    backup and the restored database is verified before committing.
    """
    await _require_admin(db, actor_id(current_user))
    return await backup_service.restore_backup(name)

@router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_backup(name: str, db: DatabaseSession, current_user: CurrentUserDependency) -> None:
    await _require_admin(db, actor_id(current_user))
    await backup_service.delete_backup(name)

__all__ = ["router"]
