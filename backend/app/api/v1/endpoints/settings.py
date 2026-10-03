"""HHMS hospital/system settings API."""
from __future__ import annotations
from fastapi import APIRouter, Path
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.settings import HospitalRead, HospitalUpdate, NumberSequenceRead, NumberSequenceUpdate, SystemSettingRead, SystemSettingUpsert
from app.services.settings import settings_service
router = APIRouter(prefix="/settings", tags=["Administration"])
@router.get("/hospital", response_model=HospitalRead)
async def get_hospital(db: DatabaseSession, _: CurrentUserDependency): return await settings_service.get_hospital(db)
@router.put("/hospital", response_model=HospitalRead)
async def update_hospital(data: HospitalUpdate, db: DatabaseSession, _: CurrentUserDependency): return await settings_service.update_hospital(db, data)
@router.get("/system", response_model=list[SystemSettingRead])
async def list_system_settings(db: DatabaseSession, _: CurrentUserDependency): return await settings_service.list_settings(db)
@router.put("/system/{setting_key}", response_model=SystemSettingRead)
async def upsert_system_setting(data: SystemSettingUpsert, db: DatabaseSession, _: CurrentUserDependency, setting_key: str = Path(min_length=1, max_length=120)):

    return await settings_service.upsert_setting(db, setting_key, data)
@router.get("/sequences", response_model=list[NumberSequenceRead])
async def list_number_sequences(db: DatabaseSession, _: CurrentUserDependency): return await settings_service.list_sequences(db)
@router.patch("/sequences/{sequence_id}", response_model=NumberSequenceRead)
async def update_number_sequence(sequence_id: int, data: NumberSequenceUpdate, db: DatabaseSession, _: CurrentUserDependency): return await settings_service.update_sequence(db, sequence_id, data)
__all__ = ["router"]
