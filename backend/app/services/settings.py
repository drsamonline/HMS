"""HHMS hospital/system settings service."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DatabaseException, DuplicateResourceException, ResourceNotFoundException
from app.models.hospital import Hospital
from app.models.number_sequence import NumberSequence
from app.models.system_setting import SystemSetting
from app.schemas.settings import HospitalUpdate, NumberSequenceUpdate, SystemSettingUpsert

class SettingsService:
    async def get_hospital(self, db: AsyncSession) -> Hospital:
        row = (await db.execute(select(Hospital).order_by(Hospital.id).limit(1))).scalar_one_or_none()
        if row is None: raise ResourceNotFoundException("Hospital profile is not configured.")
        return row
    async def update_hospital(self, db: AsyncSession, data: HospitalUpdate) -> Hospital:
        row = (await db.execute(select(Hospital).order_by(Hospital.id).limit(1))).scalar_one_or_none()
        values = data.model_dump()
        try:
            if row is None:
                row = Hospital(**values); db.add(row)
            else:
                for k,v in values.items(): setattr(row,k,v)
                row.updated_at = datetime.now(timezone.utc)
            await db.commit(); await db.refresh(row); return row
        except IntegrityError as exc:
            await db.rollback(); raise DuplicateResourceException("Hospital code already exists.") from exc
        except SQLAlchemyError as exc:
            await db.rollback(); raise DatabaseException("Unable to save hospital profile.") from exc
    async def list_settings(self, db: AsyncSession) -> list[SystemSetting]:
        return list((await db.execute(select(SystemSetting).order_by(SystemSetting.setting_key))).scalars().all())
    async def upsert_setting(self, db: AsyncSession, key: str, data: SystemSettingUpsert) -> SystemSetting:
        row = (await db.execute(select(SystemSetting).where(SystemSetting.setting_key == key))).scalar_one_or_none()
        if row is None: row = SystemSetting(setting_key=key, **data.model_dump()); db.add(row)
        elif row.is_editable:
            for k,v in data.model_dump().items(): setattr(row,k,v)
        else: raise ResourceNotFoundException("System setting is not editable.")
        await db.commit(); await db.refresh(row); return row
    async def list_sequences(self, db: AsyncSession) -> list[NumberSequence]:
        return list((await db.execute(select(NumberSequence).order_by(NumberSequence.sequence_name))).scalars().all())
    async def update_sequence(self, db: AsyncSession, sequence_id: int, data: NumberSequenceUpdate) -> NumberSequence:
        row = await db.get(NumberSequence, sequence_id)
        if row is None: raise ResourceNotFoundException("Number sequence not found.")
        for k,v in data.model_dump().items(): setattr(row,k,v)
        row.updated_at = datetime.now(timezone.utc); await db.commit(); await db.refresh(row); return row

settings_service = SettingsService()
__all__ = ["SettingsService", "settings_service"]
